+++
title = "Investigating Hax Annotations in the Signal SparsePostQuantumRatchet Crate"
date = "2025-12-08"
slug = "spqr_hax"
categories = [ "cryptography", "formal verification", "hax", "signal" ]
tags = [ "cryptography", "formal verification", "hax", "signal" ]
+++

In the Signal `SparsePostQuantumRatchet` (SPQR) [announcement blog post](https://signal.org/blog/spqr/), they mention that they did formal verification from the beginning of their implementation effort, first by modeling protocol candidates in ProVerif, and then by using hax annotations to extract F* models and prove them in CI:

> Once the F* models are extracted, we prove that core parts of our highly optimized implementation are correct, that function pre-conditions and post-conditions cannot be violated, and that the entire crate is panic free. That last one is a big deal. It is great for usability, of course, because nobody wants their app to crash. But it also matters for correctness. We aggressively add assertions about things we believe must be true when the protocol is running correctly - and we crash the app if they are false. With hax and F*, we prove that those assertions will never fail.

Pretty cool. What does this continuous formal verification look like in practice? Let's look at the SPQR source code to find out. 

*Note: I did this looking at commit hash [`46e387458d438b81a3485e26bf6bb44595e52073`](https://github.com/signalapp/SparsePostQuantumRatchet/commit/46e387458d438b81a3485e26bf6bb44595e52073).*

# Hax

[Hax](https://hax.cryspen.com) is an interesting tool for extracting formal models from Rust code. You write Rust code as normal, and link the implementation directly with a formal verification tool. It's a cargo subcommand, with several supported backends. 

Signal uses the F* backend for SPQR in their CI. Their [CI target](https://github.com/signalapp/SparsePostQuantumRatchet/blob/46e387458d438b81a3485e26bf6bb44595e52073/.github/workflows/hax.yml) for the hax part of their verification pipeline:

1. Deletes the committed F* models
2. Re-extracts F* models based on the hax annotations in the Rust code
3. Checks that all the proofs verify

This ensures that the extracted models stay in sync with the code. If all verifies, then you know that the annotated properties are satisfied, and you know that the checked code never panics.

Next, what are the hax annotations? We'll see a `#[hax_lib::attributes]` thrown on every impl block/struct that uses hax annotations, but other than that there are a variety of annotations - let's first take a look at proving pre- and post-conditions.

# Pre- and Post-Conditions

Very common annotations are `requires` (pre-condition) and `ensures` (post-conditions) in hax. 

## Length Constraints

The simplest examples would be simple length constraints. In `encaps1` in [incremental_mlkem768.rs](https://github.com/signalapp/SparsePostQuantumRatchet/blob/46e387458d438b81a3485e26bf6bb44595e52073/src/incremental_mlkem768.rs#L46) we see an example:

```rust
/// Encapsulate with header to get initial ciphertext.
#[hax_lib::requires(hdr.len() == 64)]
#[hax_lib::ensures(|(ct1,es,ss)| ct1.len() == 960 && es.len() == 2080 && ss.len() == 32)]
pub fn encaps1<R: Rng + CryptoRng>(
    hdr: &Header,
    rng: &mut R,
) -> (Ciphertext1, EncapsulationState, Secret) {
    [...]
}
```

In the first `requires` annotation, we see a pre-condition establishing that the length of the provided encapsulation key header is 64 bytes. This is a property that _callers_ must guarantee when calling the function:

```rust
#[hax_lib::requires(hdr.len() == 64)]
```

The post-condition `ensures` annotation, where we can see that we can combine constraints with `&&` to constrain the lengths of the first ciphertext, the encapsulation key, and the shared secret:

```rust
#[hax_lib::ensures(|(ct1,es,ss)| ct1.len() == 960 && es.len() == 2080 && ss.len() == 32)]
```

The `ensures` annotation is a property that the annotated _function_ must guarantee. The verifier proves that this property always holds when the function returns successfully. If the property cannot be proven, the verification fails.

## `assume!` Macro

If we look further into the function body of `encaps1`, we see the use of the `assume!` macro:

```rust
/// Encapsulate with header to get initial ciphertext.
#[hax_lib::requires(hdr.len() == 64)]
#[hax_lib::ensures(|(ct1,es,ss)| ct1.len() == 960 && es.len() == 2080 && ss.len() == 32)]
pub fn encaps1<R: Rng + CryptoRng>(
    hdr: &Header,
    rng: &mut R,
) -> (Ciphertext1, EncapsulationState, Secret) {
    let mut randomness = [0u8; libcrux_ml_kem::SHARED_SECRET_SIZE];
    rng.fill_bytes(&mut randomness);
    let mut state = vec![0u8; incremental::encaps_state_len()];
    let mut ss = vec![0u8; libcrux_ml_kem::SHARED_SECRET_SIZE];
    let ct1 = incremental::encapsulate1(hdr.as_slice(), randomness, &mut state, &mut ss);
    hax_lib::assume!(ct1.is_ok());
    hax_lib::assume!(state.len() == 2080 && ss.len() == 32);
    (
        ct1.expect("should only fail based on sizes, all sizes should be correct")
            .value
            .to_vec(),
        state,
        ss,
    )
}
```

In this case, they use the `assume!` macro to tell the verifier facts that might be hard to prove directly. Specifically, in this case they assume the state length is 2080 bytes and the shared secret length is 32 bytes. This is useful when making assumptions about dependencies: here, the function calls into the `libcrux` family of crates (most of which are verified), so the assumptions are likely based on properties guaranteed by those verified dependencies.

## Method Contracts

A more interesting example of a pre-condition can be found in `ChainEpochDirection::next_key(&mut self)` in [chain.rs](https://github.com/signalapp/SparsePostQuantumRatchet/blob/46e387458d438b81a3485e26bf6bb44595e52073/src/chain.rs#L221):

```Rust
#[hax_lib::attributes]
impl ChainEpochDirection {
    // [...]

    #[hax_lib::requires(self.next.len() > 0 && self.ctr < u32::MAX)]
    fn next_key(&mut self) -> (u32, Vec<u8>) {
        let (idx, key) = Self::next_key_internal(&mut self.next, &mut self.ctr);
        (idx, key.to_vec())
    }
```

Here they check that whenever `ChainEpochDirection::next_key` is called:

1. there is indeed a next key, and
2. the internal counter will not overflow.

This pattern of preventing overflows appears in multiple places throughout the codebase ([e.g. another example](https://github.com/signalapp/SparsePostQuantumRatchet/blob/46e387458d438b81a3485e26bf6bb44595e52073/src/chain.rs#L139)). 

# Refinements

The `refines` attribute is used to specify properties that must be true of struct fields. In this struct definition of `HeaderSent` in [chain.rs](https://github.com/signalapp/SparsePostQuantumRatchet/blob/46e387458d438b81a3485e26bf6bb44595e52073/src/v1/unchunked/send_ek.rs#L44):

```Rust
#[cfg_attr(test, derive(Clone))]
#[hax_lib::attributes]
pub struct HeaderSent {
    pub epoch: Epoch,
    auth: authenticator::Authenticator,
    #[hax_lib::refine(ek.len() == 1152)]
    ek: incremental_mlkem768::EncapsulationKey,
    #[hax_lib::refine(dk.len() == 2400)]
    dk: incremental_mlkem768::DecapsulationKey,
}
```

They ensure that when this struct is used in the codebase, the decapsulation and encapsulation keys will be of the expected length.

# Loops

For and while loops get special annotations to prove properties about each loop iteration, and to prove that they terminate. 

The `loop_invariant!` annotation specifies what must be true at the start of each loop iteration. In this example in `PolyConst<N>::lagrange_interpolate_pt` in [polynomial.rs](https://github.com/signalapp/SparsePostQuantumRatchet/blob/46e387458d438b81a3485e26bf6bb44595e52073/src/encoding/polynomial.rs#L361):

```Rust
    /// Create the Lagrange poly for `pts[i]` in `pts`, which computes
    /// f(pts[i].x) == pts[i].y, and f(pts[*].x) == 0 for all other points.
    #[hax_lib::requires(i < N && pts.len() >= N && N > 0)]
    const fn lagrange_interpolate_pt(pts: &[Pt], i: usize) -> Self {
        let pi = &pts[i];
        let mut p = Self {
            coefficients: [GF16::ZERO; N],
        };
        p.coefficients[0] = GF16::ONE;
        let mut denominator = GF16::ONE;
        {
            // const for loop
            let mut j: usize = 0;
            while j < N {
                hax_lib::loop_invariant!(j <= N);
                hax_lib::loop_decreases!(N - j);
                let pj = &pts[j];
                j += 1;
                if pi.x.value == pj.x.value {
                    continue;
                }
                // p.coefficients[N - 1].value == 0
                p = p.mult_xdiff(pj.x);
                denominator = denominator.const_mul(&pi.x.const_sub(&pj.x));
            }
        }
        // mul_assign(pi.y / denominator)
        p.mult(pi.y.const_div(&denominator))
    }
```

The `loop_decreases!` annotation specifies a value that decreases with each loop iteration, which proves that the loop terminates. In the example above, the while loop runs while `j < N`, and `loop_decreases!(N - j)` shows that `N - j` decreases each iteration (since `j` increases), ensuring the loop will eventually exit.

# Verification Control

## Opaque

There are a few methods/functions annotated with `opaque` to denote that the verifier should just treat this function as an opaque black box, i.e. it won't extract the function body at all, but it will still respect pre/post conditions. For example, in [`KeyHistory::gc`](https://github.com/signalapp/SparsePostQuantumRatchet/blob/46e387458d438b81a3485e26bf6bb44595e52073/src/chain.rs#L145):

```rust
    #[hax_lib::opaque] // ordering of slices needed
    fn gc(&mut self, current_key: u32, params: &pqrpb::ChainParams) {
        [...]
    }
```

From the comment it's clear why this is done: the function uses a language feature that hax doesn't support, so the verifier treats it as an opaque black box.

## Verification Status

If opaque is overkill, you can set the verification status to "lax" like in [`KeyHistory::gc`](https://github.com/signalapp/SparsePostQuantumRatchet/blob/46e387458d438b81a3485e26bf6bb44595e52073/src/encoding/gf.rs#L199)

```Rust
#[inline]
#[hax_lib::fstar::verification_status(lax)] // proving absence of overflow in loop condition is tricky
pub fn parallel_mult(a: GF16, into: &mut [GF16]) {
    let mut i = 0;
    while i + 2 <= into.len() {
        hax_lib::loop_decreases!(into.len() - i);
        (into[i].value, into[i + 1].value) = mul2_u16(a.value, into[i].value, into[i + 1].value);
        i += 2;
    }
    if i < into.len() {
        into[i] *= a;
    }
}
```

The `verification_status(lax)` annotation provides a nice incremental way to start using hax on an existing codebase, allowing you to mark functions for later verification while still getting some guarantees.

# FStar

You can also inject FStar statements directly or customize the options through which the proofs are generated, with `hax_lib::fstar!` or `#[hax_lib::fstar::options(...)]` respectively.

For example they use `fstar::options` to set the F* "fuel" parameter manually in [`KeyHistory::gc`](https://github.com/signalapp/SparsePostQuantumRatchet/blob/46e387458d438b81a3485e26bf6bb44595e52073/src/encoding/gf.rs#L372): 

```Rust
    #[hax_lib::fstar::options("--fuel 2")]
    #[hax_lib::ensures(|result| fstar!(r#"
        let open Spec.GF16 in
        to_bv result == 
        poly_mul (to_bv a) (to_bv b)"#))]
    const fn poly_mul(a: u16, b: u16) -> u32 {
        // [...]
    }
```

Looking at the [F* docs](https://fstar-lang.org/tutorial/book/under_the_hood/uth_smt.html#recursive-functions-and-fuel), the fuel parameter relates to proof extraction for recursive functions, controlling how many recursive steps the verifier will unroll. 

# Summary

This post explored how Signal uses hax annotations to formally verify their SPQR implementation in CI. Some of the most common annotations are:

* *Pre- and post-conditions*: `requires` and `ensures` specify what callers must guarantee and what functions must provide. These are used frequently in the codebase for length constraints and overflow prevention.

* *Refinements*: `refine` attach invariants directly to struct fields, ensuring properties like key lengths are maintained throughout the code.

* *Loop annotations*: `loop_invariant!` and `loop_decreases!` prove loop properties on each iteration and that the loop terminates.

* *Verification control*: `opaque` and `verification_status` provide escape hatches for code that's difficult to verify, allowing incremental adoption of formal verification.

* *F\* integration*: `fstar!` and `fstar::options` enables direct interaction with the F* verifier for complex proofs.

The result is a codebase where important properties are proven correct and panics are impossible. This is a powerful approach to building high assurance software that seems way easier to approach than a lot of formal verification tools. 
