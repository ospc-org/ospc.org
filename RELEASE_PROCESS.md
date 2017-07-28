This document formalizes a process for releasing new taxcalc,
og-usa, b-tax, webapp-public, and taxpuf packages to ospc.org. More
fundamentally, it is meant to facilitate compatibility across
these open source projects.

### Assigned Upstream Project (UP) Contributors
    - Tax-Calculator: @martinholmer or @matthjensen
    - OG-USA: @rickecon or @jdebacker 
    - Webapp-public: @brittainhard
    - B-Tax: @jdebacker 
    - TaxData/taxpuf: @andersonfrailey or @hdoupe


### Process

1. Upstream project (UP) tags a new release with changelog.
    - Responsibility: Assigned UP contributor
    - Should test locally first against latest release of all projects
      further upstream.  
    - In the case of an independent webapp-public update, release is not
      tagged, but commit to be released is identified. 
2. Build new conda package and release in the main channel. 
    - Responsibility: Assigned UP contributor
    - Should make and test a dev release first, but don't need to involve
      other projects. 
    - N/A for independent webapp-public updates. 
3. Email policybrains-modelers mailing list w/ package name and changelog
    - Responsibility: Assigned UP contributor
3. Test webapp-public with _new_ UP package and _existing_ versions of other
   repos: taxcalc, b-tax, og-usa, webapp-public
    - Responsibility: @hdoupe
    - Testing steps should be described in more detail in testing
      documentation. 
    - Note that projects other than webapp-public that are dependent on the
      _new_ package should be independently testing during this period as
      well. 
4. If failure, email policybrains-modelers mailing list with a description of
   the failure. 
    - Responsibility: @hdoupe
    - If failure was caught through manual inspection, add a new failing test
      to the webapp-public test suite. 
5. Any project that could be causing the failure: run test suite, add new
   failing test if none are already failing, fix incompatibility, and release
   new package, starting with step 1 from this document. 
    - Responsibility: Assigned UP contributor. 
    - UP assignee, email back to list w link to issue. 
6. Once all packages are updated and everything appears to work, deploy
   webapp-public test app. 
    - Responsibility: @brittainhard training @hdoupe
7. Email the policybrains-modelers list that everything is online at the test
   app for the next 1 full business day
    - Responsibility: @hdoupe 
8. Anyone who wants to review, reviews. 
    - Recommended, anyone who contributed to a change incorporated in the
      new package(s)
    - An assigned contributor tests. [Need a document that describes what the
      tests should be.] 
    - Write back to mailing list with any problems (return to step 4). 
9. Deploy to the main app
    - Responsibility: @brittainhard training @hdoupe