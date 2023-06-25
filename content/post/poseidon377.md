---
title: "Poseidon377, our instantiation of a SNARK-friendly hash"
date: 2022-12-05T18:50:23-04:00
draft: false
categories: [ "cryptography", "hash functions" ]
tags: [ "cryptography" ]
---

Penumbra is building a shielded, cross-chain network for private transactions, staking, swaps, and marketmaking. We use zero-knowledge proofs (ZKP) to provide privacy. One crucial component for efficient ZKPs is a hash function that is efficient in the circuit context. In this blog post we provide an overview of the hash function Poseidon, introduce Poseidon377 - our instantiation of the Poseidon ZKP-friendly hash for the Penumbra system - and two of its dependent crates which are generic over Arkworks prime fields: [`poseidon-permutation`][crates-io-poseidon-permutation], which provides an independent implementation of the Poseidon permutation, and [`poseidon-paramgen`][crates-io-poseidon-paramgen], which provides a [fully audited][audit-report] (by NCC Group in Summer 2022) and independent implementation of Poseidon parameter generation.

*Note: I wrote this blog for the Penumbra Labs site. You can see the original post [here](https://penumbra.zone/blog/poseidon377).*

### SNARK-friendly hashes

Penumbra ensures that state transitions are valid while protecting privacy using ZKPs, specifically ZK-SNARKs (Zero-Knowledge Succinct Non-Interactive ARgument of Knowledge). One of the challenges building ZK-SNARKs is the inefficiency of traditional hash algorithms like the SHA2 family, which are designed to use many bitwise operations. This makes them fast when executing on a CPU, but prohibitively slow in the context of a SNARK circuit, where bitwise operations are very expensive, as each bit must be represented by a single constraint.

For the Penumbra protocol, we need to hash in-circuit in many places. For example, we want to prove that:
* A [balance commitment][balance-commitment], which is used to check the value balance of a Penumbra transaction, was computed correctly,
* A [note commitment][note-commitment] was computed correctly, which are used to track all existing notes in Penumbra’s [tiered commitment tree][TCT],
* A [nullifier][nullifier] was derived correctly, which are used to prevent double-spends,
* A note was previously included in [Penumbra’s (Merkle) tiered commitment tree][TCT], which ensures only existing notes can be spent.

Poseidon, [first introduced by Lorenzo Grassi, Dmitry Khovratovich, Christian Rechberger, Arnab Roy, and Markus Schofnegger][poseidon-paper], is a cryptographic hash function that is efficient in the context of a SNARK circuit using R1CS arithmetization, due to the fact it operates natively over field elements.

### How Poseidon works

Poseidon uses a [sponge construction][sponge-construction], wherein the internal state is populated from some input elements, often described as the elements being “absorbed” by the sponge. A fixed-length internal permutation is applied to that internal state. Output elements are then extracted — or “squeezed”—  from the internal state. 

The inner Poseidon permutation is a substitution-permutation network, similar to AES, except instead of operating over an internal state in the form of a matrix of bytes, it operates over an internal state of a vector of field elements in some specified prime field. The permutation consists of rounds, where each round has the following steps:

* **AddRoundConstants**: where constants are added to the internal state,
* **SubWords**: where the S-box `S(x)=x^α` is applied to the internal state,
* **MixLayer**: where a matrix is multiplied with the internal state.

The total number of rounds we denote by `R`. There are two types of round in the Poseidon construction, partial and full. We denote the number of partial and full rounds by `R_P​` and `R_F`​ respectively.

### Partial vs Full Rounds

In a full round in the **SubWords** layer, the S-box is applied to each element of the internal state, as shown in the diagram below:


```plaintext
  ┌───────────────────────────────────────────────────────────┐
  │                                                           │
  │                     AddRoundConstants                     │
  │                                                           │
  └────────────┬──────────┬──────────┬──────────┬─────────────┘
               │          │          │          │              
             ┌─▼─┐      ┌─▼─┐      ┌─▼─┐      ┌─▼─┐            
             │ S │      │ S │      │ S │      │ S │            
             └─┬─┘      └─┬─┘      └─┬─┘      └─┬─┘            
               │          │          │          │              
  ┌────────────▼──────────▼──────────▼──────────▼─────────────┐
  │                                                           │
  │                         MixLayer                          │
  │                                                           │
  └────────────┬──────────┬──────────┬──────────┬─────────────┘
               │          │          │          │              
               ▼          ▼          ▼          ▼              
```

In a partial round in the **SubWords** layer, we apply the S-box only to one element of the internal state, as shown in the diagram below:

```
               │          │          │          │              
               │          │          │          │              
  ┌────────────▼──────────▼──────────▼──────────▼─────────────┐
  │                                                           │
  │                     AddRoundConstants                     │
  │                                                           │
  └────────────┬──────────────────────────────────────────────┘
               │                                               
             ┌─▼─┐                                             
             │ S │                                             
             └─┬─┘                                             
               │                                               
  ┌────────────▼──────────────────────────────────────────────┐
  │                                                           │
  │                         MixLayer                          │
  │                                                           │
  └────────────┬──────────┬──────────┬──────────┬─────────────┘
               │          │          │          │              
               ▼          ▼          ▼          ▼              
```

We apply half the full rounds (`R_f​=R_F​/2`) first, then we apply the `R_P​` partial rounds, then the rest of the `R_f​` full rounds. This approach - wherein the middle layer consists of partial rounds, and is sandwiched by full rounds - is called the [HADES design strategy][HADES] in the literature.

### Poseidon377, our poseidon implementation

[`poseidon377`][poseidon377] is our instantiation of Poseidon over the [decaf377][decaf377] group. It is a thin wrapper exposing only the [fixed-width hash functions][fixed-width] we need for the Penumbra protocol. The bulk of the interesting logic is in two dependent general-purpose Rust crates: `poseidon-permutation`, and `poseidon-paramgen`.

Crate [`poseidon-permutation`][poseidon-permutation] is an optimized implementation of the Poseidon permutation. The optimized Poseidon permutation uses sparse matrices in the partial layers to reduce the number of multiplications that need to be performed, resulting in [significant speedups][perf]: the number of multiplications in the partial layers goes from quadratic in the size of the internal state to linear. This is especially important for instantiations of Poseidon with a large width or a large number of partial rounds. 

### Parameter Generation

For an instantiation of Poseidon, the parameters we need to generate consist of:
* S-box: choosing the exponent `α` for the S-box in **SubWords** step where `S(x)=x^α`,
* Round numbers: the numbers of partial and full rounds, i.e. `R_P` and `R_F`,
* Round constants: the constants to be added in the **AddRoundConstants** step,
* MDS Matrix: generating a [Maximum Distance Separable (MDS) matrix][MDS] to use in the **MixLayer**, where we multiply this matrix by the internal state.

The problem of Poseidon parameter generation is to pick secure choices for the parameters to use in the permutation given the field, desired security level `M` in bits, as well as the width `t` of the hash function one wants to instantiate (i.e. 1:1 hash, 2:1 hash, etc.). 

One of the challenges with the Poseidon hash function is there is not a universal set of parameters. A useful analogy is if traditional CPUs had different types of bits, let’s say Blue bits and Red bits, and you had to customize SHA2 for whether you want to run it on a system with Red bits or Blue bits. While there may be optimizations that are platform-specific in traditional hash functions, the hash function itself is the same. This is not the case with Poseidon, where the parameters that define the function depend on the underlying finite field.

The Poseidon paper provides sample implementations of both the Poseidon permutation as well as parameter generation. There is a Python script called `calc_round_numbers.py` which provides secure choices for the round numbers given the security level `M`, the width of the hash function `t`, as well as the choice of S-box to use. There is also a Sage script, which generates the round numbers, constants, and Maximum Distance Separable (MDS) matrix, given the security level `M`, the width of the hash function `t`, as well as the choice of S-box.

Since the publication of the Poseidon paper, others have edited these scripts for their own projects, resulting in a number of implementations being in use derived from these initial scripts. Of particular note is [Filecoin, who have an implementation of Poseidon and parameter generation in Rust][filecoin-ht]. As an independent check, we elected to implement Poseidon parameter generation in Rust from the original paper using the Arkworks family of crates which we use throughout Penumbra’s cryptography libraries.

Our [`poseidon-paramgen`][poseidon-paramgen] crate is the result: an independent implementation of Poseidon parameter generation that generates parameters based on the desired security level in bits, the desired width of the hash function, and the prime modulus of the field. We checked each step as described in the paper, and additionally automated the S-box parameter selection step. It also includes logic to generate code containing the parameters in Rust [at build time][build-script], which we use for `poseidon377`. We describe in further detail the process of generating each parameter in our documentation [here][paramgen-docs].

### Audit Results

NCC Group performed an audit of the parameter generation code in Summer 2022. No vulnerabilities were found. The detailed public report can be found [here][audit-report]. A huge thanks to NCC Group for their many helpful suggestions throughout the audit process!

[audit-report]: https://research.nccgroup.com/2022/09/12/public-report-penumbra-labs-decaf377-implementation-and-poseidon-parameter-selection-review/
[balance-commitment]: https://protocol.penumbra.zone/main/protocol/value_commitments.html
[note-commitment]: https://protocol.penumbra.zone/main/protocol/notes/note_commitments.html
[TCT]: https://penumbra.zone/blog/tiered-commitment-tree
[nullifier]: https://protocol.penumbra.zone/main/concepts/notes_nullifiers_trees.html
[poseidon-paper]: https://eprint.iacr.org/2019/458.pdf
[sponge-construction]: https://link.springer.com/chapter/10.1007/978-3-540-78967-3_11
[HADES]: https://eprint.iacr.org/2020/179
[poseidon377]: https://github.com/penumbra-zone/poseidon377/
[decaf377]: https://github.com/penumbra-zone/decaf377/
[fixed-width]: https://rustdoc.penumbra.zone/main/poseidon377/index.html
[poseidon-permutation]: https://rustdoc.penumbra.zone/main/poseidon_permutation/index.html
[perf]: https://github.com/penumbra-zone/poseidon377/pull/21
[resources]: https://guide.penumbra.zone/main/resources.html
[filecoin-ht]: https://github.com/filecoin-project/neptune
[poseidon-paramgen]: https://rustdoc.penumbra.zone/main/poseidon_paramgen/index.html
[build-script]: https://github.com/penumbra-zone/poseidon377/blob/main/poseidon377/build.rs
[paramgen-docs]: https://protocol.penumbra.zone/main/crypto/poseidon/paramgen.html
[crates-io-poseidon-paramgen]: https://crates.io/crates/poseidon-paramgen
[crates-io-poseidon-permutation]: https://crates.io/crates/poseidon-permutation
[MDS]: https://en.wikipedia.org/wiki/MDS_matrix
