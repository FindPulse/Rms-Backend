import React from "react";

function App() {
  const handleConnect = () => {
    window.location.href = "http://localhost:8000/connect_google";
  };

  return (
    <div style={{ textAlign: "center", marginTop: "100px" }}>
      <h1>Connect Google Business Profile</h1>
      <button
        style={{ padding: "10px 20px", fontSize: "18px", cursor: "pointer" }}
        onClick={handleConnect}
      >
        Connect Now
      </button>
    </div>
  );
}

export default App;
