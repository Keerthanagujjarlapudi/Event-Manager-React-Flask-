import { Routes, Route, Navigate } from "react-router-dom";
import Nav from "./components/Nav";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Events from "./pages/Events";
import CreateEvent from "./pages/CreateEvent";
import MyRegistrations from "./pages/MyRegistrations";
import CheckIn from "./pages/CheckIn";

import Checkout from "./pages/Checkout";
import PaymentSuccess from "./pages/PaymentSuccess";
import PaymentCancel from "./pages/PaymentCancel";

export default function App() {
  return (
    <div>
      <Nav />
      <Routes>
        <Route path="/" element={<Events />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route path="/create-event" element={<CreateEvent />} />
        <Route path="/my-registrations" element={<MyRegistrations />} />
        <Route path="/checkin" element={<CheckIn />} />

        <Route path="/checkout/:eventId" element={<Checkout />} />
        <Route path="/payment/success" element={<PaymentSuccess />} />
        <Route path="/payment/cancel" element={<PaymentCancel />} />

        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </div>
  );
}
