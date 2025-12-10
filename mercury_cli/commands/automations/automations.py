from mercury_cli.globals import MERCURY_CLI
from yaspin import yaspin
from action_completer import Empty
from mercury_cli.utils.service_group_id_callable import (
    _get_group_id_completions,
    _get_service_provider_id_completions,
)
from mercury_ocip.automate.base_automation import AutomationResult
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style

completer = MERCURY_CLI.completer()

completer.automations.display_meta = "Automation operations for various entities"


@completer.automations.action(
    "find_alias", display_meta="Find the given entity behind an alias"
)
@completer.param(
    _get_service_provider_id_completions,
    display_meta="Service Provider ID",
    cast=str,
)
@completer.param(_get_group_id_completions, display_meta="Group ID", cast=str)
@completer.param(Empty, display="alias", display_meta="Alias Number", cast=str)
def _find_alias(service_provider_id: str, group_id: str, alias: str):
    """
    Find the entity behind a given alias.

    Args:
        alias_name: The name of the alias to look up.
    """
    try:
        spinner = yaspin(text="Looking up alias...", color="cyan")
        spinner.start()
    except ValueError:
        spinner = None
        print("Looking up alias...")

    try:
        result = MERCURY_CLI.agent().automate.find_alias(
            group_id=group_id,
            service_provider_id=service_provider_id,
            alias=alias,
        )

        if spinner:
            spinner.text = ""

        if result is None:
            msg = f"✘ Alias '{alias}' not found."
            if spinner:
                spinner.fail(msg)
            else:
                print(msg)
            return

        if result.ok:
            entity_id = getattr(
                result.payload.entity, "service_user_id", None
            ) or getattr(result.payload.entity, "user_id", None)

            msg = f"✔ Alias '{alias}' found: {entity_id}"
            if spinner:
                spinner.ok(msg)
            else:
                print(msg)
        else:
            msg = f"✘ Alias '{alias}' not found."
            if spinner:
                spinner.fail(msg)
            else:
                print(msg)

    except Exception as e:
        if spinner:
            spinner.fail("✘ Error occurred during alias lookup.")
        print(f"Error: {e}")


def _format_audit_output(
    result: AutomationResult,
) -> tuple[FormattedText, Style]:
    """Format audit result with nice styling using prompt_toolkit."""

    style = Style.from_dict(MERCURY_CLI.css())

    output = []
    audit = result.payload

    # Header
    output.append(("class:header", "\n╔══════════════════════════════════════════╗\n"))
    output.append(("class:header", "║        GROUP AUDIT REPORT                ║\n"))
    output.append(("class:header", "╚══════════════════════════════════════════╝\n"))

    # Group Details Section
    if audit.group_details:
        details = audit.group_details
        output.append(("class:subheader", "\n📋 GROUP DETAILS\n"))
        output.append(("class:separator", "─" * 80 + "\n"))

        output.append(("class:label", "  Group Name:              "))
        output.append(("class:value", f"{details.group_name or 'N/A'}\n"))

        output.append(("class:label", "  Group ID:                "))
        output.append(("class:value", f"{details.group_id or 'N/A'}\n"))

        output.append(("class:label", "  Service Provider ID:     "))
        output.append(("class:value", f"{details.service_provider_id or 'N/A'}\n"))

        output.append(("class:label", "  Default Domain:          "))
        output.append(("class:value", f"{details.default_domain or 'N/A'}\n"))

        if hasattr(details, "user_count") and hasattr(details, "user_limit"):
            output.append(("class:label", "  User Count:              "))
            output.append(
                ("class:value", f"{details.user_count} / {details.user_limit}\n")
            )

        output.append(("class:label", "  Time Zone:               "))
        output.append(
            (
                "class:value",
                f"{details.time_zone_display_name or details.time_zone or 'N/A'}\n",
            )
        )

        if hasattr(details, "calling_line_id_name"):
            output.append(("class:label", "  Calling Line ID Name:    "))
            output.append(("class:value", f"{details.calling_line_id_name or 'N/A'}\n"))

        if hasattr(details, "calling_line_id_phone_number"):
            output.append(("class:label", "  Calling Line ID Phone:   "))
            output.append(
                ("class:value", f"{details.calling_line_id_phone_number or 'N/A'}\n")
            )

        if hasattr(details, "calling_line_id_display_phone_number"):
            output.append(("class:label", "  Display Phone Number:    "))
            output.append(
                (
                    "class:value",
                    f"{details.calling_line_id_display_phone_number or 'N/A'}\n",
                )
            )

    # License Breakdown - Group Services
    output.append(("class:subheader", "\n🔧 GROUP SERVICES AUTHORIZATION\n"))
    output.append(("class:separator", "─" * 80 + "\n"))
    if (
        audit.license_breakdown
        and audit.license_breakdown.group_services_authorization_table
    ):
        for service, count in sorted(
            audit.license_breakdown.group_services_authorization_table.items()
        ):
            output.append(("class:label", f"  {service:<40} "))
            output.append(("class:value", f"{count:>5}\n"))
    else:
        output.append(("class:label", "  No group services found\n"))

    # License Breakdown - Service Packs
    output.append(("class:subheader", "\n📦 SERVICE PACKS AUTHORIZATION\n"))
    output.append(("class:separator", "─" * 80 + "\n"))
    if (
        audit.license_breakdown
        and audit.license_breakdown.service_packs_authorization_table
    ):
        for pack, count in sorted(
            audit.license_breakdown.service_packs_authorization_table.items()
        ):
            output.append(("class:label", f"  {pack:<40} "))
            output.append(("class:value", f"{count:>5}\n"))
    else:
        output.append(("class:label", "  No service packs found\n"))

    # License Breakdown - User Services
    output.append(("class:subheader", "\n👤 USER SERVICES AUTHORIZATION\n"))
    output.append(("class:separator", "─" * 80 + "\n"))
    if (
        audit.license_breakdown
        and audit.license_breakdown.user_services_authorization_table
    ):
        for service, count in sorted(
            audit.license_breakdown.user_services_authorization_table.items()
        ):
            output.append(("class:label", f"  {service:<40} "))
            output.append(("class:value", f"{count:>5}\n"))
    else:
        output.append(("class:label", "  No user services found\n"))

    # Group DNs
    output.append(("class:subheader", "\n📞 GROUP DIRECTORY NUMBERS\n"))
    output.append(("class:separator", "─" * 80 + "\n"))
    if audit.group_dns:
        output.append(("class:label", "  Total DNs: "))
        output.append(("class:value", f"{audit.group_dns.total}\n"))

        if audit.group_dns.numbers:
            sorted_numbers = sorted(
                audit.group_dns.numbers,
                key=lambda x: int(x) if x.isdigit() else float("inf"),
            )
            numbers_str = ", ".join(sorted_numbers)
            max_line_length = 76
            if len(numbers_str) <= max_line_length:
                output.append(("class:value", f"  {numbers_str}\n"))
            else:
                words = numbers_str.split(", ")
                current_line = "  "
                for word in words:
                    if (
                        len(current_line) + len(word) + 2 > max_line_length
                        and current_line.strip()
                    ):
                        output.append(("class:value", current_line.rstrip() + "\n"))
                        current_line = "  " + word + ", "
                    else:
                        current_line += word + ", "
                if current_line.strip():
                    output.append(
                        ("class:value", current_line.rstrip().rstrip(",") + "\n")
                    )
        else:
            output.append(("class:label", "  No directory numbers found\n"))
    else:
        output.append(("class:label", "  Directory number information not available\n"))

    output.append(("class:divider", "\n" + "─" * 80 + "\n\n"))

    return FormattedText(output), style


@completer.automations.action(
    "group_audit", display_meta="Perform a comprehensive audit of a group"
)
@completer.param(
    _get_service_provider_id_completions,
    display_meta="Service Provider ID",
    cast=str,
)
@completer.param(_get_group_id_completions, display_meta="Group ID", cast=str)
def _group_audit(service_provider_id: str, group_id: str):
    """
    Perform a comprehensive audit of a group.

    Args:
        service_provider_id: The ID of the service provider.
        group_id: The ID of the group to audit.
    """
    try:
        spinner = yaspin(text="Performing group audit...", color="cyan")
        spinner.start()
    except ValueError:
        spinner = None
        print("Performing group audit...")

    try:
        result = MERCURY_CLI.agent().automate.audit_group(
            service_provider_id=service_provider_id,
            group_id=group_id,
        )

        if spinner:
            spinner.stop()

        if result.ok:
            formatted_output, style = _format_audit_output(result)
            print_formatted_text(formatted_output, style=style)
        else:
            msg = f"✘ Group audit failed for Group ID '{group_id}'."
            if spinner:
                spinner.fail(msg)
            else:
                print(msg)

    except Exception as e:
        if spinner:
            spinner.fail("✘ Error occurred during group audit.")
        print(f"Error: {e}")
