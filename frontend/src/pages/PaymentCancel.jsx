import { useNavigate } from "react-router-dom";

export default function PaymentCancel() {
  const nav = useNavigate();
  return (
    <div className="container">
      <div className="card card-pad">
        <h2 className="title">Payment Cancelled</h2>
        <p className="subtitle">You can try again.</p>
        <button className="btn btn-primary" onClick={() => nav("/")}>
          Back to Events
        </button>
      </div>
    </div>
  );
}
