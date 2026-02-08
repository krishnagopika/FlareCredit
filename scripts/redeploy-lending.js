import "dotenv/config";
import hre from "hardhat";
import { ethers } from "ethers";
import { readFileSync } from "fs";

async function main() {
  const connection = await hre.network.connect();
  const provider = new ethers.BrowserProvider(connection.provider);
  const signer = await provider.getSigner();
  console.log("Deploying with:", signer.address);

  // Existing contract addresses (keep oracle + token)
  const ORACLE_ADDRESS = process.env.ORACLE_ADDRESS || "0xa87209410af28367472073Cebf8cbac86c802Bb7";
  const TOKEN_ADDRESS = process.env.TOKEN_ADDRESS || "0x45c7B48d002D014D0F8C8dff55045016AD28ACCB";

  console.log("Using existing Oracle:", ORACLE_ADDRESS);
  console.log("Using existing Token:", TOKEN_ADDRESS);

  // Build first
  await hre.tasks.getTask("build").run({ quiet: true, noTests: true });

  // Deploy new MockLending
  const artifact = JSON.parse(
    readFileSync("./artifacts/contracts/MockLending.sol/MockLending.json", "utf8")
  );
  const factory = new ethers.ContractFactory(artifact.abi, artifact.bytecode, signer);
  const lending = await factory.deploy(ORACLE_ADDRESS, TOKEN_ADDRESS);
  await lending.waitForDeployment();
  const lendingAddr = await lending.getAddress();
  console.log("New MockLending deployed at:", lendingAddr);

  // Fund lending pool with 500k mUSDC from token contract
  const tokenArtifact = JSON.parse(
    readFileSync("./artifacts/contracts/MockLoanToken.sol/MockLoanToken.json", "utf8")
  );
  const token = new ethers.Contract(TOKEN_ADDRESS, tokenArtifact.abi, signer);

  const agentBalance = await token.balanceOf(signer.address);
  console.log("Agent mUSDC balance:", ethers.formatUnits(agentBalance, 18));

  const fundAmount = ethers.parseUnits("500000", 18);
  if (agentBalance >= fundAmount) {
    const tx = await token.transfer(lendingAddr, fundAmount);
    await tx.wait();
    console.log("Funded lending pool with 500,000 mUSDC");
  } else {
    console.log("WARNING: Not enough mUSDC to fund pool. Transfer manually.");
    console.log("Available:", ethers.formatUnits(agentBalance, 18));
  }

  await connection.close();

  console.log("\n=== UPDATE THESE ===");
  console.log("LENDING_ADDRESS=" + lendingAddr);
  console.log("(Oracle and Token addresses remain the same)");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
