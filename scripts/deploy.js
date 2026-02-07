import hre from "hardhat";
import { ethers } from "ethers";
import { readFileSync } from "fs";

async function main() {
  // Connect to the network specified via --network flag
  const connection = await hre.network.connect();
  const provider = new ethers.BrowserProvider(connection.provider);
  const signer = await provider.getSigner();
  console.log("Deploying with:", signer.address);

  // Helper to deploy a contract
  async function deploy(name, args = []) {
    const artifact = JSON.parse(
      readFileSync(`./artifacts/contracts/${name}.sol/${name}.json`, "utf8")
    );
    const factory = new ethers.ContractFactory(artifact.abi, artifact.bytecode, signer);
    const contract = await factory.deploy(...args);
    await contract.waitForDeployment();
    const addr = await contract.getAddress();
    console.log(`${name} deployed at: ${addr}`);
    return { contract, addr };
  }

  // Compile first
  await hre.tasks.getTask("build").run({ quiet: true, noTests: true });

  // 1. Deploy fake money (mUSDC)
  const token = await deploy("MockLoanToken");

  // 2. Deploy credit oracle
  const oracle = await deploy("FlareCreditOracle");

  // 3. Deploy lending (no collateral — just oracle + token)
  const lending = await deploy("MockLending", [oracle.addr, token.addr]);

  // 4. Fund lending pool with 500k mUSDC
  const fundAmount = ethers.parseUnits("500000", 18);
  const tx = await token.contract.transfer(lending.addr, fundAmount);
  await tx.wait();
  console.log("Funded lending pool with 500,000 mUSDC");

  // Close connection
  await connection.close();

  console.log("\n--- SAVE THESE ADDRESSES ---");
  console.log("MOCK_TOKEN=" + token.addr);
  console.log("ORACLE=" + oracle.addr);
  console.log("LENDING=" + lending.addr);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
