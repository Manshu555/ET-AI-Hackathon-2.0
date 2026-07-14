require('dotenv').config();
const express = require('express');
const cors = require('cors');
const cookieParser = require('cookie-parser');
const sqlite3 = require('sqlite3').verbose();
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { OAuth2Client } = require('google-auth-library');
const path = require('path');

const app = express();
const PORT = 5000;

// Configuration
const JWT_SECRET = 'super_secret_key_change_in_production'; // Must match Python backend exactly
const JWT_REFRESH_SECRET = 'super_secret_refresh_key_change_in_production';
const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID || '';

const googleClient = new OAuth2Client(GOOGLE_CLIENT_ID);

// Middleware
app.use(express.json());
app.use(cookieParser());
app.use(cors({
  origin: true, // Allow all origins for dev, or specify frontend URL
  credentials: true,
}));

// Database Setup - Connect to exactly the same DB as Python
const dbPath = path.resolve(__dirname, '../backend/epc_intel.db');
const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('Error connecting to database:', err);
  } else {
    console.log('✅ Connected to shared SQLite database');

    // Create users table if it doesn't exist (mirrors Python models.py)
    db.run(`
      CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT,
        role TEXT NOT NULL,
        google_id TEXT UNIQUE,
        auth_provider TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
  }
});

// Helper for generating UUIDs
const generateUuid = () => require('crypto').randomUUID();

// Helper to wrap db.get in a promise
const dbGet = (sql, params) => new Promise((resolve, reject) => {
  db.get(sql, params, (err, row) => err ? reject(err) : resolve(row));
});

// Helper to wrap db.run in a promise
const dbRun = (sql, params) => new Promise((resolve, reject) => {
  db.run(sql, params, function (err) {
    if (err) reject(err);
    else resolve(this);
  });
});

// ==========================================
// ROUTES
// ==========================================

app.post('/api/v1/auth/register', async (req, res) => {
  try {
    const { name, email, password, role } = req.body;

    const existing = await dbGet('SELECT * FROM users WHERE email = ?', [email]);
    if (existing) {
      return res.status(409).json({ detail: 'The user with this email already exists in the system' });
    }

    const salt = await bcrypt.genSalt(10);
    const password_hash = await bcrypt.hash(password, salt);
    const id = generateUuid();

    await dbRun(
      'INSERT INTO users (id, name, email, password_hash, role, auth_provider) VALUES (?, ?, ?, ?, ?, ?)',
      [id, name, email.toLowerCase(), password_hash, role || 'engineer', 'local']
    );

    res.status(201).json({ id, name, email, role: role || 'engineer' });
  } catch (err) {
    console.error(err);
    res.status(500).json({ detail: 'Registration failed' });
  }
});


app.post('/api/v1/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    const user = await dbGet('SELECT * FROM users WHERE email = ?', [email.toLowerCase()]);
    if (!user || !user.password_hash) {
      return res.status(401).json({ detail: 'Incorrect email or password' });
    }

    const isMatch = await bcrypt.compare(password, user.password_hash);
    if (!isMatch) {
      return res.status(401).json({ detail: 'Incorrect email or password' });
    }

    // Issue identical JWT format as Python
    const exp = Math.floor(Date.now() / 1000) + (15 * 60); // 15 mins
    const accessToken = jwt.sign({ exp, sub: user.id, role: user.role }, JWT_SECRET);

    const refExp = Math.floor(Date.now() / 1000) + (7 * 24 * 60 * 60); // 7 days
    const refreshToken = jwt.sign({ exp: refExp, sub: user.id, type: 'refresh' }, JWT_REFRESH_SECRET);

    res.cookie('refresh_token', refreshToken, { httpOnly: true, secure: false, sameSite: 'lax' });

    res.json({
      access_token: accessToken,
      user: { id: user.id, name: user.name, email: user.email, role: user.role }
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ detail: 'Login failed' });
  }
});


app.post('/api/v1/auth/google', async (req, res) => {
  try {
    const { access_token } = req.body;

    // Fetch user info using the access token
    const googleRes = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
      headers: { Authorization: `Bearer ${access_token}` }
    });

    if (!googleRes.ok) {
      throw new Error('Failed to fetch user info from Google');
    }

    const payload = await googleRes.json();
    const googleEmail = payload.email.toLowerCase();
    const googleName = payload.name || 'Google User';
    const googleSub = payload.sub;

    let user = await dbGet('SELECT * FROM users WHERE email = ?', [googleEmail]);

    if (user) {
      // Link account
      if (!user.google_id) {
        await dbRun('UPDATE users SET google_id = ? WHERE id = ?', [googleSub, user.id]);
      }
    } else {
      // Create account
      const id = generateUuid();
      await dbRun(
        'INSERT INTO users (id, name, email, role, google_id, auth_provider) VALUES (?, ?, ?, ?, ?, ?)',
        [id, googleName, googleEmail, 'engineer', googleSub, 'google']
      );
      user = await dbGet('SELECT * FROM users WHERE id = ?', [id]);
    }

    const exp = Math.floor(Date.now() / 1000) + (15 * 60);
    const accessToken = jwt.sign({ exp, sub: user.id, role: user.role }, JWT_SECRET);

    const refExp = Math.floor(Date.now() / 1000) + (7 * 24 * 60 * 60);
    const refreshToken = jwt.sign({ exp: refExp, sub: user.id, type: 'refresh' }, JWT_REFRESH_SECRET);

    res.cookie('refresh_token', refreshToken, { httpOnly: true, secure: false, sameSite: 'lax' });

    res.json({
      access_token: accessToken,
      user: { id: user.id, name: user.name, email: user.email, role: user.role }
    });
  } catch (err) {
    console.error(err);
    res.status(401).json({ detail: 'Invalid Google token' });
  }
});


app.post('/api/v1/auth/refresh', async (req, res) => {
  const token = req.cookies.refresh_token;
  if (!token) return res.status(401).json({ detail: 'No refresh token provided' });

  try {
    const payload = jwt.verify(token, JWT_REFRESH_SECRET);
    if (payload.type !== 'refresh') throw new Error();

    const user = await dbGet('SELECT * FROM users WHERE id = ?', [payload.sub]);
    if (!user) throw new Error();

    const exp = Math.floor(Date.now() / 1000) + (15 * 60);
    const accessToken = jwt.sign({ exp, sub: user.id, role: user.role }, JWT_SECRET);

    const refExp = Math.floor(Date.now() / 1000) + (7 * 24 * 60 * 60);
    const newRefreshToken = jwt.sign({ exp: refExp, sub: user.id, type: 'refresh' }, JWT_REFRESH_SECRET);

    res.cookie('refresh_token', newRefreshToken, { httpOnly: true, secure: false, sameSite: 'lax' });

    res.json({
      access_token: accessToken,
      user: { id: user.id, name: user.name, email: user.email, role: user.role }
    });
  } catch (err) {
    res.status(401).json({ detail: 'Invalid or expired refresh token' });
  }
});

app.post('/api/v1/auth/logout', (req, res) => {
  res.clearCookie('refresh_token');
  res.json({ message: 'Logged out' });
});

app.listen(PORT, () => {
  console.log(`🚀 Node.js Auth Microservice running on http://localhost:${PORT}`);
});
