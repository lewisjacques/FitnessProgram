@staticmethod
def get_sheet_conditional_formats(list_of_sheet_responses:list, sheet_id:int):
    for sheet_resp in list_of_sheet_responses:
        if sheet_id == sheet_resp["properties"]["sheetId"]:
            return(sheet_resp.get('conditionalFormats', []))

def get_clear_conditional_formatting_req(
    self,
    sheet_id:int,
    start_row:int,
    end_row:int,
    start_col:int,
    end_col:int
):
    """
    Run with the following in sheets.py

        conditional_formatting_req = \
            self.get_clear_conditional_formatting_req(
                sheet_id=sheet_id,
                start_row=start_row,
                end_row=end_row,
                start_col=start_col,
                end_col=end_col
            )

    Args:
        sheet_id (int): _description_
        start_row (int): _description_
        end_row (int): _description_
        start_col (int): _description_
        end_col (int): _description_
    """
    # Get all conditional formatting rules
    response = self.service.spreadsheets().get(
        spreadsheetId=self.spreadsheet_id,
        fields="sheets.properties,sheets.conditionalFormats"
    ).execute()

    conditional_formats = self.get_sheet_conditional_formats(
        response["sheets"], sheet_id
    )

    # Prepare requests to modify rules only for the specified range
    modify_requests = []
    for i, rule in enumerate(conditional_formats):

        ranges = rule['ranges']
        # Track whether the rule should be modified
        new_ranges = []
        needs_modification = False

        # Modify the ranges to exclude the specified range
        for r in ranges:
            # Check if the rule's range intersects with the specified range
            if not (start_row >= r['endRowIndex'] or end_row <= r['startRowIndex'] or
                    start_col >= r['endColumnIndex'] or end_col <= r['startColumnIndex']):
                # If there's an intersection, we modify the range
                needs_modification = True
                
                # Splitting the range
                if r['startRowIndex'] < start_row:
                    print("Keeping top proportion of the formatting")
                    # Keep the top portion
                    new_ranges.append({
                        'sheetId': sheet_id,
                        'startRowIndex': r['startRowIndex'],
                        'endRowIndex': start_row,
                        'startColumnIndex': r['startColumnIndex'],
                        'endColumnIndex': r['endColumnIndex']
                    })
                if r['endRowIndex'] > end_row:
                    print("Keeping bottom proportion of the formatting")
                    # Keep the bottom portion
                    new_ranges.append({
                        'sheetId': sheet_id,
                        'startRowIndex': end_row,
                        'endRowIndex': r['endRowIndex'],
                        'startColumnIndex': r['startColumnIndex'],
                        'endColumnIndex': r['endColumnIndex']
                    })
                if r['startColumnIndex'] < start_col:
                    print("Keeping left proportion of the formatting")
                    # Keep the left portion
                    new_ranges.append({
                        'sheetId': sheet_id,
                        'startRowIndex': max(r['startRowIndex'], start_row),
                        'endRowIndex': min(r['endRowIndex'], end_row),
                        'startColumnIndex': r['startColumnIndex'],
                        'endColumnIndex': start_col
                    })
                if r['endColumnIndex'] > end_col:
                    print("Keeping right proportion of the formatting")
                    # Keep the right portion
                    new_ranges.append({
                        'sheetId': sheet_id,
                        'startRowIndex': max(r['startRowIndex'], start_row),
                        'endRowIndex': min(r['endRowIndex'], end_row),
                        'startColumnIndex': end_col,
                        'endColumnIndex': r['endColumnIndex']
                    })
            else:
                # If no intersection, keep the range unchanged
                new_ranges.append(r)

        # If the rule needs modification, update it
        if needs_modification:
            modify_requests.append({
                "updateConditionalFormatRule": {
                    "rule": {
                        "ranges": new_ranges,
                        "booleanRule": rule.get('booleanRule', {})
                    },
                    "index": i,
                    "sheetId": sheet_id
                }
            })

    return(modify_requests)
