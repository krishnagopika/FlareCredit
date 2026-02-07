import "dotenv/config";

export default {
  solidity: "0.8.20",
  networks: {
    coston2: {
      type: "http",
      url: process.env.RPC_URL,
      accounts: [process.env.PRIVATE_KEY],
    },
  },
};
