+++
date = "2018-03-30"
title = "Visualizing Cosmological Power Spectra with d3.js"
slug = "visualizing-cosmological-power-spectra"
categories = [ "Post", "Cosmology", "JavaScript", "d3.js"]
tags = [ "astrophysics", "cosmology", "d3.js", "visualization" ]
+++

Cosmologists make observations of galaxies and radiation in the universe to constrain parameters of the [Lambda CDM model ](https://en.wikipedia.org/wiki/Lambda-CDM_model), which is the model that best describes our current understanding of the universe.
These cosmological parameters include quantities like &Omega;<sub>m</sub> and &Omega;<sub>&Lambda;</sub>,
which describe the matter and [dark energy](https://en.wikipedia.org/wiki/Dark_energy) content of the universe respectively.

Two key observables that constrain these parameters are the **matter power spectrum** and the **angular power spectrum of the Cosmic Microwave Background** (CMB) radiation. Let's briefly go over what each of these observables describes.

## Matter Power Spectrum

The matter power spectrum - *P(k)* - describes the large scale structure of the universe - it tells us
on which scales matter is distributed. *P(k)* is a function of _wavenumber_ *k* which *k* corresponds
to inverse scale - so _increasing_ wavenumber means _decreasing_ scale.

For example, using [the visualization](https://redshiftzero.github.io/cosmowebapp/), we can see that by increasing the matter content of the universe, we
increase the power at large wavenumber, which corresponds to smaller scales.
This occurs due to enhanced structure formation as a result of the additional matter content.

## CMB Angular Power Spectrum

The Cosmic Microwave Background (CMB) radiation was produced only ~100,000 years after the Big Bang, and gives us information about the universe at these early times. One observable from this radiation is the CMB angular power spectrum, which describes anisotropies in the temperature of the CMB radiation as a function of *angular scale*. Since this temperature anisotropy is defined over a sphere, the temperature anisotropy is separated out into angular scales using a multipole expansion (to read how this multipole expansion is done in detail, check out [these notes (PDF)](http://www.helsinki.fi/~hkurkisu/cpt/Cosmo12.pdf)). The spectrum *C<sub>ℓ</sub>* (plotted as *ℓ(ℓ+1)C<sub>ℓ</sub>*) is a function of multipole *ℓ*, so *_increasing_* multipole corresponds to *decreasing* angular scales.

## Visualizing Power Spectra

*Note: This visualization was created in collaboration with [Eric Baxter](https://ebaxter.github.io/), astrophysics postdoc at UPenn.*

To visualize how these power spectra change as a function of cosmological parameters,
we used `d3.js`, a popular JavaScript library for creating interactive visualizations.

## <center>[Launch the visualization here!](https://redshiftzero.github.io/cosmowebapp/)</center>

As the user moves a given slider, the spectra are updated by linearly interpolating between the nearest pre-computed spectra.
To create the pre-computed spectra, we used [CAMB](https://camb.info/), a software package for computing power spectra based on input cosmological parameters to generate power and CMB spectra around a fiducial value. We selected a fiducial model from the [2015 results from the Planck Collaboration (PDF)](https://arxiv.org/pdf/1502.01589.pdf). The universe was kept spatially flat (i.e. &Omega;<sub>m</sub> + &Omega;<sub>&Lambda;</sub> = 1) both because it is a well established constraint and to reduce the amount of data that we needed to generate with CAMB.

If you'd like to check out the code, it's available [here on GitHub](https://github.com/redshiftzero/cosmowebapp). If you'd like to learn more about the effect of cosmological parameters on the power spectra, check out [this tutorial](http://background.uchicago.edu/~whu/intermediate/intermediate.html).
