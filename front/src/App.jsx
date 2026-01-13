import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home.jsx";
import Chat from "./pages/Chat.jsx";
import Films from "./pages/Films.jsx";
import About from "./pages/About.jsx";
import "./App.css";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/chat" element={<Chat />} />
      <Route path="/films" element={<Films />} />
      <Route path="/about" element={<About />} />
    </Routes>
  );
}
