+++
date = "2020-11-10"
title = "Continuous threat modeling, Part 1: Tooling wish list"
slug = "continuous-threat-modeling"
categories = [ "Post", "threat modeling"]
tags = [ "security", "threat modeling" ]
+++

# Motivation

When performing software-centric threat-modeling on an application[^1], one typically:

1. generates at least one Data Flow Diagram (DFD) or other diagrams that model the software,
2. enumerates threats using the diagram(s) as an aid, and then
3. determines which mitigations should be applied.

Automated tools can potentially aid the threat modeler in each of these stages. When the design of a system is modified, the threat modeling exercise may be performed again, resulting in needing to pass through the above steps again. Even if a design remains static, the threats and mitigations should still be evaluated periodically as the threat landscape may evolve, e.g. if attacker capabilities or motivations change. This means that tools or processes that can aid the threat modeler perform these tasks on a continuous basis can be of great value.

# Tooling to aid these steps

When going about the above steps, several questions immediately come up, some of which have existing solutions in the ecosystem, and some of which do not.

### How to generate and store the diagrams?

For an initial iteration, taking a picture of a sketch or whiteboard drawing can be sufficient. On an continuous basis having the DFD elements and data flows stored in a version-controllable format like XML (as [draw.io](http://draw.io/) does), YAML (as [threagile](https://github.com/Threagile/threagile) or [threat-modeling](https://github.com/freedomofpress/threat-modeling) does) or directly as code (as [pytm](https://github.com/izar/pytm) does) is ideal. All of these tools enable one to generate the data flow diagrams from the version controlled DFD data.

Some tools like [OWASP Threat Dragon](https://owasp.org/www-project-threat-dragon/), [Microsoft's TMT](https://docs.microsoft.com/en-us/azure/security/develop/threat-modeling-tool) and draw.io also provide a GUI to aid in this step.

### How to enumerate and store threats?

Some of the above mentioned tools provide assistance for the threat enumeration process, using an existing methodology like STRIDE-per-element (in the case of Microsoft TMT and Threat Dragon), although these can only be used as an aid and need to be critically evaluated by the threat modeler to determine their relevance, and to add other potentially relevant threats. The threat modeling may also use existing attack libraries (like [MITRE CAPEC](https://capec.mitre.org/)) to aid in threat enumeration.

In terms of storing the threats once enumerated, a first-order approach is to use an existing ticketing system (e.g. a private GitHub repository) or a spreadsheet to store enumerated threats.

The advantage of a ticketing system is that it's easy to crosslink with mitigations or individual development tickets being implemented. The downside is that it's not easy (as it is with a spreadsheet) to e.g. sort all threats by risk score, which you might do in order to determine which are the most important threats on which to focus your engineering effort.

The downside of the spreadsheet approach is that it's a bit awkward to perform deeper analysis on, as well as follow one-to-many relationships. But, the spreadsheet has the advantage of being something that one can export as CSV and store in version control (although not in the most readable format, but one could then load the CSV in e.g. [pandas](https://pandas.pydata.org/) if one wants to perform further analysis).

Some tools like [threagile](https://github.com/Threagile/threagile), [threat-modeling](https://github.com/freedomofpress/threat-modeling), and [pytm](https://github.com/izar/pytm) store the enumerated threats in YAML, JSON, and in the case of pytm, a SQL dump. These all enable easy analysis using other tools as well as for YAML and JSON human-readable storage in version control.

### How to determine which mitigations to apply?

Once threats have been enumerated, next we need to decide how to make decisions about them. If we can mitigate all threats, then great. However, we might be unable to completely mitigate all threats, so we need to decide how to allocate the engineering effort we have in a rational manner to manage the risk. There are not a lot of tools that aid in this dimension (see the next section on Simulation-like question answering).

*Edit 11/12/2020*: Another important aspect here is how best to store the mitigations - and their mapping to threats. It is highly useful to track which mitigations map to which threats such that developers can clearly see the purpose of the mitigation, and to enable one to evaluate the impact of removing a given security control (e.g. if debates arise on their importance due to maintenance burden or user impact). In [threat-modeling](https://github.com/freedomofpress/threat-modeling), the approach is to store the mitigations also in YAML, similar to the threats, with references to the threat IDs they apply to, to enable this sort of analysis[^2].

# Ideas

Next, here are some directions that I think would be useful to explore further.

### Integration in CI/CD pipelines

The [threatspec folks](https://github.com/threatspec/threatspec) suggest integrating their tool (which is quite cool and involves adding annotations directly in the application code) as part of a CI/CD pipeline performing report or DFD generation.

One could also imagine deeper integration in CI/CD pipelines. For example, by parsing the DFD, threats, and mitigations data, in CI one could flag issues like:

* Dataflow has no threats enumerated for it (i.e. threats are missing)
* Threats have no status (i.e. a decision needs to be made to accept, transfer, mitigate, etc.)

Or inconsistencies in the DFD data itself to guide system modelers, e.g.:

* No trust boundaries present (there should be at least one trust boundary)
* Process element lacks entry or exit dataflow (there should be an entry and an exit)

This is [explored](https://github.com/freedomofpress/threat-modeling#linter) in the [threat-modeling](https://github.com/freedomofpress/threat-modeling) tool ([ticket](https://github.com/freedomofpress/threat-modeling/issues/52)).

### Simulation-like question answering

As a system designer we often ask questions like (see ticket [here](https://github.com/freedomofpress/threat-modeling/issues/49)):

* What happens if I remove mitigation X? How much does total risk increase?
* I only have time to implement one complex mitigation, is it rational to implement mitigation X or mitigation Y?

A tool that can aid in answering these questions (in a lightweight fashion), e.g. by recomputing the total risk score when a mitigation is removed or added, could be very helpful in decision-making. Of course a pre-requisite here is the accuracy of the risk scores - if they are very uncertain, that may need to be factored into the analysis (e.g. as is done in [FAIR (Factor Analysis of Information Risk) risk framework](https://www.fairinstitute.org/)).

The only tool I'm aware of in this direction is [the SPARTA tool](https://distrinet.cs.kuleuven.be/software/sparta/#) from KU Leuven which allows one to both rank risks as well as answer some simulation-type questions using an approach based on the FAIR risk framework.

### Attack tree (or attack graph) generation

While the exercise of generating attack trees manually is a useful one for system designers (as is threat enumeration), one could also imagine at least partially automating the generation of attack trees.

When an attacker is able to successfully realize a given threat as an attack, other threats become accessible, e.g. once one is able to get code execution in a VM, they can next attempt to exploit a bug in the hypervisor. One could annotate threats with these child-parent relationships to indicate which threats become accessible once the given threat is realized, and from that derive attack trees. This is the approach taken [here](https://github.com/freedomofpress/threat-modeling/blob/main/threat_modeling/threats.py#L185-L213) in the [threat-modeling](https://github.com/freedomofpress/threat-modeling) tool[^3].

# Fin

If you have thoughts on this or know of tools or approaches (especially if FLOSS 😇) that address the above concerns, feel free to drop me a note on [Twitter](https://twitter.com/redshiftzero) or by [email](mailto:jen@redshiftzero.com).

[^1]: A lot has already been written on the benefits of doing threat modeling so I'm not going to espouse the benefits here.
[^2]: Armed with this mitigations data, one could do a "resilience" sort of test here, where one could simulate the impact of the failure of a given countermeasure: pick a given countermeasure, disable it, what is the impact of disabling this mitigation? If it's significant, then this shows an area where one should focus additional effort to provide defense in depth.
[^3]: One could also imagine various ways of removing the parent-child threat annotation requirement, e.g. perhaps one could have the system designer specify the likely entry-point threats on the attack surface of the system. At this point provided there is a mapping of threats to DFD elements, the rest of the process could be automated: the entry-point threats are root nodes, and then one follows the dataflows to grow the rest of the attack tree, adding a child node in the attack tree for every threat associated with the destination node.
