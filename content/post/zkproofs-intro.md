---
title: "Bringing Zero-Knowledge Proofs to Penumbra"
date: 2023-03-07T18:50:23-04:00
draft: false
categories: [ "cryptography", "zero-knowledge proofs" ]
tags: [ "cryptography" ]
---

Shielded blockchains like Penumbra provide privacy through the use of zero-knowledge proofs (ZKPs): actions that change the public chain state can be verified _without_ providing the underlying private data. 

*Note: I wrote this blog for the Penumbra Labs site. Below is an abbreviated version. You can see the original post [here](https://penumbra.zone/blog/zkproofs-intro/).*

### Transparent "Proofs"

[Our plan][penumbra-dev-plan] for implementing Penumbra has been to use an approach which allows quick iterations on the design of the system without spending significant effort each iteration to update zero-knowledge circuits. To ensure that the design of the system was kept compatible with zero-knowledge proofs, each action had a “transparent proof”, for example for spending notes:

```Rust
/// Transparent proof for spending existing notes.
///
/// This structure keeps track of the auxiliary (private) inputs.
#[derive(Clone, Debug)]
pub struct SpendProof {
   // Inclusion proof for the note commitment.
   pub state_commitment_proof: tct::Proof,
   // The note being spent.
   pub note: Note,
   // The blinding factor used for generating the value commitment.
   pub v_blinding: Fr,
   // The randomizer used for generating the randomized spend auth key.
   pub spend_auth_randomizer: Fr,
   // The spend authorization key.
   pub ak: VerificationKey<SpendAuth>,
   // The nullifier deriving key.
   pub nk: keys::NullifierKey,
}


impl SpendProof {
   /// Called to verify the proof using the provided public inputs.
   ///
   /// The public inputs are:
   /// * the merkle root of the state commitment tree,
   /// * value commitment of the note to be spent,
   /// * nullifier of the note to be spent,
   /// * the randomized verification spend key,
   pub fn verify(
       &self,
       anchor: tct::Root,
       balance_commitment: balance::Commitment,
       nullifier: Nullifier,
       rk: VerificationKey<SpendAuth>,
   ) -> anyhow::Result<()> {
      // ...
}
```

This `SpendProof` struct trivially stored the witnesses in cleartext. The prover created this struct, and sent it to the node, where a verification method was called using the public inputs provided in the transaction. The verification method did all the integrity checks the real proof would: verifying the Merkle path, checking the prover had an opening of the public commitment, and so on. This did _not_ provide privacy, but it let us rapidly prototype the system while refining the protocol design, with assurance that when our requirements became stable, we could fill in the proofs.

### Zero-Knowledge

As we approach mainnet and the system functionality becomes stable, we began migrating from transparent proofs to zero-knowledge proofs starting with [testnet 46, codenamed Lysithea][testnet46], released on February 27th, 2023. Now that Penumbra’s multi-asset shielded pool is stable, that release migrated outputs (actions that create new notes) and spends (actions that consume existing notes) to use zero-knowledge proofs. Interaction with Penumbra’s DEX, governance, and staking systems will follow. 

One of Penumbra’s design goals is to create a usable privacy system. That means fast proving times: at mainnet we’re aiming for proving times below one second on end-user devices. We can do this by performing the proving for all actions concurrently and by using Groth16. For Penumbra’s initial ZKPs, we use the pairing-friendly BLS12-377 proving curve and the [Arkworks implementation of the Groth16 proving system][arkworks-groth16]. It has excellent out-of-the-box performance even before optimization: on an M1 macbook, transactions with three actions (one spend, two outputs) typically take under 1.3s to generate. We also get the benefits of very small proof size and using a mature system that has been in production for years.

A disadvantage of Groth16 is that it requires a circuit-specific setup, meaning each time we change our proof statements, we need to re-run a decentralized setup procedure to generate new parameters for the prover and verifier. The requirement for this process is there is at least one honest participant in the setup, thus motivating a large setup process involving many participants. Stay tuned for more details on the setup procedure and how you can participate!

Our Spend proof from above now looks like this:

```Rust
pub struct SpendProof(Proof<Bls12_377>);


impl SpendProof {
   pub fn prove<R: CryptoRng + Rng>(
       rng: &mut R,
       pk: &ProvingKey<Bls12_377>,
       state_commitment_proof: tct::Proof,
       note: Note,
       v_blinding: Fr,
       spend_auth_randomizer: Fr,
       ak: VerificationKey<SpendAuth>,
       nk: NullifierKey,
       anchor: tct::Root,
       balance_commitment: balance::Commitment,
       nullifier: Nullifier,
       rk: VerificationKey<SpendAuth>,
   ) -> anyhow::Result<Self> {
       let circuit = SpendCircuit {
           state_commitment_proof,
           note,
           v_blinding,
           spend_auth_randomizer,
           ak,
           nk,
           anchor,
           balance_commitment,
           nullifier,
           rk,
       };
       let proof = Groth16::prove(pk, circuit, rng).map_err(|err| anyhow::anyhow!(err))?;
       Ok(Self(proof))
   }


   /// Called to verify the proof using the provided public inputs.
   pub fn verify(
       &self,
       vk: &PreparedVerifyingKey<Bls12_377>,
       anchor: tct::Root,
       balance_commitment: balance::Commitment,
       nullifier: Nullifier,
       rk: VerificationKey<SpendAuth>,
   ) -> anyhow::Result<()> {
      // ...
   }
}
```

Our ZK proofs are now just three group elements in size. The prover uses provided proving parameters (type `ProvingKey<Bls12_377>`), which we distribute via a `penumbra-proof-params` crate, to create the proof using their private witnesses and public inputs. The verifier uses the corresponding verifying key (type `PreparedVerifyingKey<Bls12_377>`) in order to verify the proofs on the node using the public inputs provided in the transaction. 

### Circuit Programming

To generate the circuit for each action, we first need to represent the statements we want to prove - for example that the prover knows an opening of a specific public commitment - in a way that our proving system can understand. For Groth16 proofs, this means representing all statements to be proved in-circuit as a rank-1 constraint system (R1CS). We need to be able to write down elliptic curve operations, hash function evaluations and so on, as a number of constraint equations that are simple linear combinations of field element variables.

Several of our dependencies now have this R1CS functionality: [`decaf377`][decaf377], [`poseidon377`][poseidon377], and [`penumbra-tct`][penumbra-tct] all have an optional `r1cs` feature, while `penumbra-crypto` has R1CS functionality inline next to each type that needs to be represented in-circuit. This lets us do elliptic curve operations, SNARK-friendly hashing, and all other operations in-circuit. For example, here is the type that represents in-circuit which path a node in our [tiered commitment tree][tct-blog] can take:

```Rust
/// Represents the different paths a quadtree node can take.
///
/// A bundle of boolean R1CS constraints representing the path.
pub struct WhichWayVar {
    /// The node is the leftmost (0th) child.
    pub is_leftmost: Boolean<Fq>,
    /// The node is the left (1st) child.
    pub is_left: Boolean<Fq>,
    /// The node is the right (2nd) child.
    pub is_right: Boolean<Fq>,
    /// The node is the rightmost (3rd) child.
    pub is_rightmost: Boolean<Fq>,
}
```

We can see in-circuit the path of the node at a given height is represented by four boolean constraints. The `Fq` type here just represents the type of the field elements used by the proving system.

These R1CS types are used during constraint synthesis. We write Rust code to define types that define bundles of constraints. We then use those types along with the Arkworks `ConstraintSystem<Fq>`, which internally keeps track of all the R1CS constraints we build up by:
* allocating witness or input variables, 
* defining constants, or 
* performing an operation on defined variables or constants.  

An upstream Arkworks trait called `ConstraintSynthesizer` is implemented for each of our circuit/actions. Here’s part of the implementation for our Spend circuit:

```Rust
impl ConstraintSynthesizer<Fq> for SpendCircuit {
  fn generate_constraints(self, cs: ConstraintSystemRef<Fq>) -> ark_relations::r1cs::Result<()> {
    // Witnesses
    let note_var = note::NoteVar::new_witness(cs.clone(), || Ok(self.note.clone()))?;
    …
    let v_blinding_vars = UInt8::new_witness_vec(cs.clone(), self.v_blinding.to_bytes())?;

    // Public inputs
    let claimed_balance_commitment_var =
    BalanceCommitmentVar::new_input(cs.clone(), || Ok(self.balance_commitment))?;
      …

    // Check integrity of balance commitment.
    let balance_commitment = note_var.value().commit(v_blinding_vars)?;
    balance_commitment
    .enforce_equal(&claimed_balance_commitment_var)?;
  
    // ...

    Ok(())
  }
}
```

In our abridged and slightly simplified constraint synthesis example here, we can see that we first witness a `NoteVar`, providing a reference to the underlying constraint system. This allocates a variable in-circuit, adding constraints as we go. 

Next, we define a public balance commitment, which represents a commitment to the value balance of this action. The public balance commitment we call `claimed_balance_commitment_var` as it represents the public value of the balance commitment: the verifier needs to certify that the balance commitment was computed correctly, using private variables it does not have access to on the `NoteVar`. The prover adds constraints to demonstrate that by calling `commit` on the value of the `NoteVar`, and adding constraints that the output of the `commit` method must be equal to the corresponding public input. 

In a similar fashion, we can build up all constraints in an ergonomic manner by writing regular Rust code. 

[penumbra-dev-plan]: https://penumbra.zone/blog/how-were-building-penumbra/
[testnet46]: https://github.com/penumbra-zone/penumbra/releases/tag/046-lysithea
[arkworks-groth16]: https://github.com/arkworks-rs/groth16
[zcash-sapling]: https://z.cash/upgrade/sapling/
[penumbra-proof-params]: https://github.com/penumbra-zone/penumbra/tree/main/proof-params/src
[decaf377]: https://github.com/penumbra-zone/decaf377
[poseidon377]: https://github.com/penumbra-zone/poseidon377
[penumbra-tct]: https://github.com/penumbra-zone/penumbra/tree/main/tct/src
[tct-blog]: https://penumbra.zone/blog/tiered-commitment-tree
[guide]: https://guide.penumbra.zone/main/index.html
