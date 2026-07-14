"use client";

export default function Loader({ text = "Loading" }: { text?: string }) {
  return (
    <div className="loader-container">
      <div className="loader">
        <span className="loader-text">{text}</span>
        <div className="load-inner load-one"></div>
        <div className="load-inner load-two"></div>
        <div className="load-inner load-three"></div>
      </div>
    </div>
  );
}
