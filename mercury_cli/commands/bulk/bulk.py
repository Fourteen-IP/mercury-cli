from mercury_cli.globals import MERCURY_CLI
from yaspin import yaspin
import traceback
import os

completer = MERCURY_CLI.completer()

completer.bulk.display_meta = "Bulk operations for various entities"


def _cli_wrap_verification(bulk_command: str, entity_name: str, **kwargs):
    """
    Wrapper to handle bulk CSV operations with spinner and error handling.

    Args:
        bulk_command: The bulk method name to call on the bulk object.
        entity_name: The name of the entity being processed (for display purposes).
        **kwargs: Additional keyword arguments, expects 'file_path'.
    """

    file_path = kwargs.get("file_path")

    # Validate file before starting spinner
    if not file_path.lower().endswith(".csv"):
        print("✘ Provided file is not a CSV.")
        return

    if not os.path.exists(file_path):
        print(f"✘ File not found: {file_path}")
        return

    try:
        spinner = yaspin(text="Processing CSV...", color="cyan")
        spinner.start()
    except ValueError:
        spinner = None
        print("Processing CSV...")

    try:
        bulk_obj = MERCURY_CLI.agent().bulk

        bulk_method = getattr(bulk_obj, bulk_command, None)

        if not bulk_method:
            raise ValueError(f"Bulk method {bulk_command} not found.")

        output = bulk_method(file_path)

        success_count = sum(1 for result in output if result.get("success", False))
        failed_rows = [result for result in output if not result.get("success", False)]
        failure_count = len(output) - success_count

        if spinner:
            spinner.text = ""

        if failure_count == 0:
            msg = f"✔ All {success_count} {entity_name} processed successfully."
            if spinner:
                spinner.ok(msg)
            else:
                print(msg)
        else:
            msg = f"✘ {failure_count} {entity_name} failed to process. {success_count} succeeded."
            if spinner:
                spinner.fail(msg)
                spinner.write("\nFailed rows details:")
                for row in failed_rows:
                    row_index = (
                        row.get("index", "Unknown") + 1
                        if isinstance(row.get("index"), int)
                        else "Unknown"
                    )
                    error_msg = (
                        row.get("response") or row.get("error") or "Unknown error"
                    )
                    detail_msg = row.get("detail") if row.get("detail") else ""
                    row_data = row.get("data", {})

                    spinner.write(f"\n  Row {row_index}:")
                    spinner.write(f"    Error: {error_msg}")
                    spinner.write(f"    Detail: {detail_msg}")
                    if row_data:
                        spinner.write(f"    Data: {row_data}")
                    if "exception" in row:
                        spinner.write(f"    Exception: {row['exception']}")
            else:
                print(msg)
                print("\nFailed rows details:")
                for row in failed_rows:
                    row_index = (
                        row.get("index", "Unknown") + 1
                        if isinstance(row.get("index"), int)
                        else "Unknown"
                    )
                    error_msg = (
                        row.get("response") or row.get("error") or "Unknown error"
                    )
                    row_data = row.get("data", {})

                    print(f"\n  Row {row_index}:")
                    print(f"    Error: {error_msg}")
                    print(f"    Detail: {detail_msg}")
                    if row_data:
                        print(f"    Data: {row_data}")
                    if "exception" in row:
                        print(f"    Exception: {row['exception']}")

    except Exception as e:
        error_details = traceback.format_exc()
        msg = f"✘ Error processing CSV: {str(e)}"
        if spinner:
            spinner.fail(msg)
            spinner.write(f"\nFull traceback:\n{error_details}")
        else:
            print(msg)
            print(f"\nFull traceback:\n{error_details}")
    finally:
        if spinner:
            spinner.stop()
