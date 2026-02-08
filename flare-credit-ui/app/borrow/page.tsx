"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import FlareCreditLogo from "@/components/FlareCreditLogo";

const stagger = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.12 },
  },
};

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: "easeOut" as const },
  },
};

export default function Borrow() {
  const maxBorrow = 25000;

  const [amount, setAmount] = useState(10000);
  const interestRate = 6.2;

  const monthlyPayment = (amount * (1 + interestRate / 100)) / 12;
  const totalRepayment = amount * (1 + interestRate / 100);

  return (
    <motion.div
      className="min-h-screen"
      variants={stagger}
      initial="hidden"
      animate="visible"
    >
      {/* Nav Bar */}
      <motion.nav
        className="glass border-b border-white/5 sticky top-0 z-40"
        variants={fadeUp}
      >
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <FlareCreditLogo size="sm" />
          <span className="text-sm text-slate-400">Loan Builder</span>
        </div>
      </motion.nav>

      <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
        {/* Borrow Power */}
        <motion.div
          className="glass rounded-2xl p-6 space-y-3"
          variants={fadeUp}
        >
          <h2 className="text-xl font-bold text-white">Borrow Power</h2>
          <motion.p
            className="text-4xl font-bold text-gradient"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
            ${maxBorrow.toLocaleString()}
          </motion.p>
          <p className="text-slate-400 text-sm">
            Based on your verified credit score
          </p>
        </motion.div>

        {/* Loan Builder */}
        <motion.div
          className="glass rounded-2xl p-6 space-y-6"
          variants={fadeUp}
        >
          <h2 className="text-xl font-bold text-white">Build Your Loan</h2>

          {/* Amount display */}
          <div className="text-center">
            <motion.p
              className="text-5xl font-bold text-white"
              key={amount}
              initial={{ scale: 1.1, opacity: 0.7 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.2 }}
            >
              ${amount.toLocaleString()}
            </motion.p>
            <p className="text-sm text-slate-400 mt-1">Loan Amount</p>
          </div>

          {/* Slider */}
          <div className="space-y-2">
            <input
              type="range"
              min={1000}
              max={maxBorrow}
              step={500}
              value={amount}
              onChange={(e) => setAmount(Number(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-slate-500">
              <span>$1,000</span>
              <span>${maxBorrow.toLocaleString()}</span>
            </div>
          </div>

          {/* Purpose */}
          <div className="space-y-2">
            <label className="text-sm text-slate-400">Loan Purpose</label>
            <select className="w-full p-3 rounded-xl text-sm">
              <option>Business</option>
              <option>Education</option>
              <option>Emergency</option>
              <option>Personal</option>
            </select>
          </div>
        </motion.div>

        {/* Loan Summary */}
        <motion.div
          className="glass rounded-2xl p-6 space-y-4"
          variants={fadeUp}
        >
          <h2 className="text-xl font-bold text-white">Loan Summary</h2>

          <div className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b border-white/5">
              <span className="text-slate-400">Interest Rate</span>
              <span className="text-white font-semibold">
                {interestRate}%
              </span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-white/5">
              <span className="text-slate-400">
                Est. Monthly Payment
              </span>
              <motion.span
                className="text-white font-semibold"
                key={monthlyPayment.toFixed(0)}
                initial={{ opacity: 0.5 }}
                animate={{ opacity: 1 }}
              >
                ${monthlyPayment.toFixed(0)}
              </motion.span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-slate-400">Total Repayment</span>
              <motion.span
                className="text-xl font-bold text-gradient"
                key={totalRepayment.toFixed(0)}
                initial={{ opacity: 0.5 }}
                animate={{ opacity: 1 }}
              >
                ${totalRepayment.toFixed(0)}
              </motion.span>
            </div>
          </div>
        </motion.div>

        {/* Submit */}
        <motion.div variants={fadeUp}>
          <motion.button
            className="btn-gradient w-full glow-blue-strong text-lg py-4"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            Submit Application &rarr;
          </motion.button>
        </motion.div>
      </div>
    </motion.div>
  );
}
