require('dotenv').config();
const express = require('express');
const cors = require('cors');
const cookieParser = require('cookie-parser');
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { OAuth2Client } = require('google-auth-library');

const app = express();
const PORT = 5000;

// Configuration
const JWT_SECRET = 'super_secret_key_change_in_production'; // Must match Python backend exactly
const JWT_REFRESH_SECRET = 'super_secret_refresh_key_change_in_production';
const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID || '';
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/epc_intel';

const googleClient = new OAuth2Client(GOOGLE_CLIENT_ID);

// Middleware
app.use(express.json());
app.use(cookieParser());
app.use(cors({
  origin: true,
  credentials: true,
}));

// Database Setup
mongoose.connect(MONGODB_URI)
  .then(() => console.log('✅ Connected to MongoDB via Mongoose'))
  .catch(err => console.error('Error connecting to MongoDB:', err));

const userSchema = new mongoose.Schema({
  _id: { type: String, required: true },
  name: { type: String, required: true },
  email: { type: String, required: true, unique: true },
  password_hash: { type: String },
  role: { type: String, required: true },
  google_id: { type: String },
  auth_provider: { type: String, required: true },
  created_at: { type: Date, default: Date.now }
});

const User = mongoose.model('User', userSchema, 'users');

const generateUuid = () => require('crypto').randomUUID();


// ==========================================
// ROUTES
// ==========================================

app.post('/api/v1/auth/register', async (req, res) => {
  try {
    const { name, email, password, role } = req.body;

    const existing = await User.findOne({ email: email.toLowerCase() });
    if (existing) {
      return res.status(409).json({ detail: 'The user with this email already exists in the system' });
    }

    const salt = await bcrypt.genSalt(10);
    const password_hash = await bcrypt.hash(password, salt);
    const id = generateUuid();

    await User.create({
      _id: id,
      name,
      email: email.toLowerCase(),
      password_hash,
      role: role || 'engineer',
      auth_provider: 'local'
    });

    res.status(201).json({ id, name, email, role: role || 'engineer' });
  } catch (err) {
    console.error(err);
    res.status(500).json({ detail: 'Registration failed' });
  }
});


app.post('/api/v1/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    const user = await User.findOne({ email: email.toLowerCase() });
    if (!user || !user.password_hash) {
      return res.status(401).json({ detail: 'Incorrect email or password' });
    }

    const isMatch = await bcrypt.compare(password, user.password_hash);
    if (!isMatch) {
      return res.status(401).json({ detail: 'Incorrect email or password' });
    }

    const exp = Math.floor(Date.now() / 1000) + (15 * 60); // 15 mins
    const accessToken = jwt.sign({ exp, sub: user._id, role: user.role }, JWT_SECRET);

    const refExp = Math.floor(Date.now() / 1000) + (7 * 24 * 60 * 60); // 7 days
    const refreshToken = jwt.sign({ exp: refExp, sub: user._id, type: 'refresh' }, JWT_REFRESH_SECRET);

    res.cookie('refresh_token', refreshToken, { httpOnly: true, secure: false, sameSite: 'lax' });

    res.json({
      access_token: accessToken,
      user: { id: user._id, name: user.name, email: user.email, role: user.role }
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ detail: 'Login failed' });
  }
});


app.post('/api/v1/auth/google', async (req, res) => {
  try {
    const { access_token } = req.body;

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

    let user = await User.findOne({ email: googleEmail });

    if (user) {
      if (!user.google_id) {
        user.google_id = googleSub;
        await user.save();
      }
    } else {
      const id = generateUuid();
      user = await User.create({
        _id: id,
        name: googleName,
        email: googleEmail,
        role: 'engineer',
        google_id: googleSub,
        auth_provider: 'google'
      });
    }

    const exp = Math.floor(Date.now() / 1000) + (15 * 60);
    const accessToken = jwt.sign({ exp, sub: user._id, role: user.role }, JWT_SECRET);

    const refExp = Math.floor(Date.now() / 1000) + (7 * 24 * 60 * 60);
    const refreshToken = jwt.sign({ exp: refExp, sub: user._id, type: 'refresh' }, JWT_REFRESH_SECRET);

    res.cookie('refresh_token', refreshToken, { httpOnly: true, secure: false, sameSite: 'lax' });

    res.json({
      access_token: accessToken,
      user: { id: user._id, name: user.name, email: user.email, role: user.role }
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

    const user = await User.findById(payload.sub);
    if (!user) throw new Error();

    const exp = Math.floor(Date.now() / 1000) + (15 * 60);
    const accessToken = jwt.sign({ exp, sub: user._id, role: user.role }, JWT_SECRET);

    const refExp = Math.floor(Date.now() / 1000) + (7 * 24 * 60 * 60);
    const newRefreshToken = jwt.sign({ exp: refExp, sub: user._id, type: 'refresh' }, JWT_REFRESH_SECRET);

    res.cookie('refresh_token', newRefreshToken, { httpOnly: true, secure: false, sameSite: 'lax' });

    res.json({
      access_token: accessToken,
      user: { id: user._id, name: user.name, email: user.email, role: user.role }
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
