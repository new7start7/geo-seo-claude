# geo-report

Use this skill when the user wants a client-facing summary based on an audit result.

## Workflow
1. Generate the JSON audit with `python run.py <url> --format json`.
2. Translate the structured checks into plain-English findings.
3. Keep the report aligned with analyzer output and avoid unsupported claims.

## Report sections
- Overview
- Scorecard
- Critical issues
- Quick wins
- Strategic GEO improvements
