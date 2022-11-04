# Where should we write the GIF?
Output qd_profile_create.gif

Set FontSize 20
Set Width 1600
Set Height 600

Type "# Let's create your first profile to run a qontract-reconcile integration"
Sleep 1s
Enter

Type "qd profile create sql-query"
Sleep 1s
Enter
Sleep 1s

Type "sql-query"
Sleep 1s
Enter

Type "--enable-deletion"
Sleep 1s
Enter

Type "# Let's review it."
Sleep 1s
Enter

Type "qd profile show sql-query"
Sleep 1s
Enter

Sleep 2s
Type "# Done"

# End
Sleep 5s
