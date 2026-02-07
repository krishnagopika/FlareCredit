"use client";

import { useState } from 'react';

export default function Borrow() {

  const maxBorrow = 25000; // later fetch from oracle

  const [amount, setAmount] = useState(10000);
  const interestRate = 6.2;

  const monthlyPayment = (amount * (1 + interestRate/100)) / 12;
  const totalRepayment = amount * (1 + interestRate/100);

  return (
    <div className="p-10 max-w-4xl mx-auto space-y-6">

      {/* Borrow Power */}
      <div className="border rounded-2xl p-6">
        <h2 className="text-xl font-bold">
          Borrow Power
        </h2>

        <p className="text-3xl font-bold text-green-600">
          ${maxBorrow.toLocaleString()}
        </p>

        <p>Based on your verified credit score ✅</p>
      </div>

      {/* Loan Builder */}
      <div className="border rounded-2xl p-6 space-y-4">

        <h2 className="text-xl font-bold">
          Build Your Loan
        </h2>

        {/* Slider */}
        <input
          type="range"
          min={1000}
          max={maxBorrow}
          step={500}
          value={amount}
          onChange={(e) => setAmount(Number(e.target.value))}
          className="w-full"
        />

        <p>Amount: <b>${amount.toLocaleString()}</b></p>

        {/* Purpose */}
        <select className="border p-2 rounded w-full">
          <option>Business</option>
          <option>Education</option>
          <option>Emergency</option>
          <option>Personal</option>
        </select>

      </div>

      {/* Loan Summary */}
      <div className="border rounded-2xl p-6 space-y-2">

        <h2 className="text-xl font-bold">
          Loan Summary
        </h2>

        <p>Interest Rate: <b>{interestRate}%</b></p>

        <p>
          Estimated Monthly Payment:
          <b> ${monthlyPayment.toFixed(0)}</b>
        </p>

        <p>
          Total Repayment:
          <b> ${totalRepayment.toFixed(0)}</b>
        </p>

      </div>

      {/* Submit */}
      <button className="bg-black text-white px-6 py-3 rounded-xl w-full">
        Submit Application →
      </button>

    </div>
  );
}
