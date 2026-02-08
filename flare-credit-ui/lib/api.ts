const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function processCreditScore(address: string) {
  const res = await fetch(`${BASE_URL}/process-score`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_address: address,
    }),
  });

  if (!res.ok) {
    throw new Error("Failed to process credit score");
  }

  return res.json();
}

export async function getLoanStatus(address: string) {
  const res = await fetch(`${BASE_URL}/loan-status/${address}`);

  if (!res.ok) {
    throw new Error("Failed to fetch loan status");
  }

  return res.json();
}

export async function evaluateLoan(
  user_address: string,
  requested_amount: number
) {
  const res = await fetch(`${BASE_URL}/evaluate-loan`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_address,
      requested_amount,
    }),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Loan evaluation failed");
  }

  return res.json();
}

export async function disburseLoan(
  user_address: string,
  requested_amount: number
) {
  const res = await fetch(`${BASE_URL}/disburse-loan`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_address,
      requested_amount,
    }),
  });

  if (!res.ok) {
    let message = `Disbursement failed (${res.status})`;
    try {
      const err = await res.json();
      message = err.detail || message;
    } catch {
      // Response wasn't JSON
    }
    throw new Error(message);
  }

  return res.json();
}

export async function getRepaymentInfo(address: string) {
  const res = await fetch(`${BASE_URL}/repayment-info/${address}`);

  if (!res.ok) {
    throw new Error("Failed to fetch repayment info");
  }

  return res.json();
}
