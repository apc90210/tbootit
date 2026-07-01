# MODULE REPORT TEMPLATE

## STATUS

`PASS / PARTIAL / FAIL`

## MODULE

`<module name>`

## DATE

`<date>`

## BRANCH

`<branch>`

## COMMIT

`<commit hash>`

## WHAT WAS DONE

- item
- item
- item

## FILES CREATED

- path
- path

## FILES MODIFIED

- path
- path

## HOW TO RUN

```powershell
Set-Location C:\tbootit
docker compose up --build
```

## HOW TO TEST

```text
Core API: http://127.0.0.1:8000
API Docs: http://127.0.0.1:8000/docs
Admin Shell: http://127.0.0.1:8010
```

## SELF-CHECKS

| Check | Result |
|---|---|
| docker compose config | PASS/FAIL |
| docker compose up --build | PASS/FAIL |
| health endpoint | PASS/FAIL |
| API smoke | PASS/FAIL |
| shell smoke | PASS/FAIL |
| tests | PASS/FAIL |

## KNOWN LIMITATIONS

- item
- item

## NEXT STEP

`<recommended next module>`
