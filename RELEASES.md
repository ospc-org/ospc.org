PolicyBrain RELEASE HISTORY
==============================
Go
[here](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pulls?q=is%3Apr+is%3Aclosed)
for a complete commit history.

Release 1.0.3 on 2017-10-05
----------------------------

**User Highlights**
- **New user-input processing logic.** which eliminated several input processing bugs. 
    - T.J. Alumbaugh designed a process in which TaxBrain GUI parameters could more easily be mapped to Tax-Calculator parameters.  Martin Holmer and Hank Doupe implemented this design.
- **New warning/error messages and logic.**
    - Martin Holmer and Hank Doupe coordinated to build this feature. 
    - There are now three outcomes for when a reform is submitted. 
        1.	If the user input does not cause any warnings or errors, then the reform is submitted to the model.
        2.	If the user input causes warnings but not errors, then the warning messages are displayed under the offending parameters.  The user has the option to either submit the reform as is or change the values.  The reform runs as usual either way.  For example, a user reduces the Standard Deduction (STD).  There is nothing illogical about this input, but the user should be aware of Tax-Calculator’s limitations.
        3.	If the user input causes errors and/or warnings, then the user will not be able to run the reform unless they fix the parameters that cause the errors.  Note: Errors are only thrown in cases where the user input is illogical.  For example, the cap for the second personal income tax bracket is set below the cap of the first personal income tax bracket.
- **New data visualization for the Cost-of-Capital calculator.**
    - Haylee Ham built a bubble plot feature that enables the user to better visualize the change in the METTR, METR, Cost of Capital, and Depreciation for several tabulations.
- **Front-end bug-fixes and enhancements**
    - Brittain Hard and Sean Wang made several contributions including improved labels and functionality for displaying a total in the “TOTAL LIABILITIES BY CALENDAR YEAR (CHANGE)” table


**Pull Requests**
- [#655](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/655) – Refactor submit_reform for quick-calc submission case – Hank Doupe
- [#656](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/656) – Elastic submit bugfix – Hank Doupe
- [#658](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/658) – Show reform contents when assumption file is not uploaded – Hank Doupe
- [#665](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/665) – Revert switches from 1/0 to True/False in model – Hank Doupe
- [#670](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/670) – Fix dynamic simulation button logic for file upload – Hank Doupe
- [#679](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/679) – Add file input warning/error handling logic – Hank Doupe
- [#687](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/687) – Bokeh Requirement in Correct File – Brittain Hard
- [#689](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/689) – Pin Bokeh to 0.12.7 – Hank Doupe

Release 1.0.2 on 2017-08-18
----------------------------

 **Pull Requests**
- [#569](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/569) – Add Table Title for Excel Output – Sean Wang
- [#583](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/583) – Update README.md – Teodora Szasz
- [#593](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/593) – File Upload Fixes – Brittain Hard
- [#599](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/599) – Revert to Tax-Calculator Version 0.9.0 – Brittain Hard
- [#603](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/603) – Bad syntax in requirements file – Brittain Hard
- [#611](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/611) – Web Page Clean Up – Sean Wang
- [#621](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/621) – Change title name for liability table – Sean Wang
- [#622](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/622) – Remove reference to commit IDs – Hank Doupe
- [#623](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/623) – Modify row labels for fiscal table – Sean Wang
- [#626](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/626) – Rename “Diagnositic Table” to “Distribution Table” – Sean Wang
- [#635](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/635) – Remove lines that were lower-casing the titles – Brittain Hard
- [#637](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/637) – Handle data from new BTAX Version – Brittain Hard
- [#641](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/641) – GUI input processing – Hank Doupe
- [#642](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/642) – Bubble plot visualization – Haylee Ham
- [#646](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/646) – Add summary row for table – Brittain Hard
- [#648](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/648) – Fix Payroll Tax + Income Tax buttons on difference table – Sean Wang
- [#650](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/650) – GUI input processing bug fixes – Hank Doupe
- [#651](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/651) – Fix BTAX backend bug caused by PR #641 – Hank Doupe
- [#652](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/652) – Refactor Reset Server Script – Brittain Hard
