"""Post-run decimal boundary correction; no change to frozen prompts or gold."""
from decimal import Decimal
import accuracy_pilot as p


def evaluate(rows,gold,coverage):
    output=p.evaluate(rows,gold,coverage);rmap={r['question_id']:r for r in rows}
    for item,expected in zip(output,gold):
        row=rmap.get(expected['question_id'])
        if row and item['answered'] and expected['expected_value'] is not None:
            item['fact_correct']=(abs(Decimal(str(row['value']))-Decimal(str(expected['expected_value'])))<=Decimal(str(expected['absolute_tolerance']))
                and all(row[k]==expected[k] for k in ('unit','period','scope')))
            item['citation_supported']=item['fact_correct'] and bool(row['evidence_refs']) and all(s in coverage.get(item['question_id'],[]) for s in row['evidence_refs'])
    return output
