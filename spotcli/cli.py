#!/usr/bin/env python3
import sys
import time

import click
import rich.console
import rich.prompt
import rich.table
import rich.traceback

import spotcli
import spotcli.configuration
import spotcli.tasks

console = rich.console.Console(highlight=False)
rich.traceback.install()


@click.group()
def main():
    pass


@click.command()
def version():
    """Get Spot CLI version."""
    console.print(f"Spot CLI version {spotcli.__version__}")


@click.command()
@click.argument("scenario")
@click.option("-y", "--auto-approve", is_flag=True, default=False, help="Skip interactive approval before executing actions")
def run(scenario, auto_approve):
    """Run a scenario.

    SCENARIO is the name of the scenario to run.
    """
    console.print(f"[bold]Spot CLI version {spotcli.__version__}")
    config = spotcli.configuration.load()
    try:
        s = config.scenarios[scenario]
        console.print(
            f"Loading scenario [bold green]{scenario}[/]"
            + f" [italic]({s.description})[/]"
            if s.description
            else ""
        )
    except KeyError:
        console.print(f"Scenario [bold red]{scenario}[/] not found")
        sys.exit(1)
    console.print("\n")
    for task in s.tasks:
        table = rich.table.Table(
            title=f"Going to [bold]{task.kind}[/] these elastigroups:"
        )
        table.add_column("ID", justify="center", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Instances", style="green")
        for target in task.targets:
            table.add_row(target.id, target.name, str(target.capacity["target"]))
        console.print(table)
        console.print("\n")
    auto_approve or rich.prompt.Confirm.ask("Continue?") or sys.exit(1)
    t_start = time.time()
    s.run()
    t_end = time.time()
    duration = t_end - t_start
    console.print(
        f"\n[bold green]Scenario run complete! Executed {len(s.tasks)} tasks in {duration:.2f} seconds."
    )


@click.command()
@click.argument("group")
@click.option("-p", "--show-processes", is_flag=True, default=False, help="Show process suspension status")
def status(group, show_processes):
    """Get elastigroup status.

    GROUP is elastigroup name, alias or regex.
    """
    console.print(f"[bold]Spot CLI version {spotcli.__version__}")
    config = spotcli.configuration.load()
    targets = spotcli.tasks.TargetList(config.providers["spot"], config.aliases, [group])
    console.print("\n")
    table = rich.table.Table(title="Elastigroup status")
    table.add_column("ID", justify="center", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Instances", style="green")
    if show_processes:
        table.add_column("Processes", style="yellow")
    for target in targets:
        if show_processes:
            processes_raw = target.processes
            processes = "\n".join(
                [
                    f"[bold]{proc}[/]: "
                    f"{'[green]' if 'active' in processes_raw[proc] else '[red]'}"
                    f"{processes_raw[proc]}[/]"
                    for proc in processes_raw
                ]
            ) + "\n"
            table.add_row(target.id, target.name, str(target.capacity["target"]), processes)
        else:
            table.add_row(target.id, target.name, str(target.capacity["target"]))
    console.print(table)
    console.print("\n")


@click.command()
@click.argument("group")
@click.option("-b", "--batch", default="20%", help="Batch size, instances or percentage")
@click.option("-g", "--grace", default="5m", help="Grace period")
@click.option("-y", "--auto-approve", is_flag=True, default=False, help="Skip interactive approval before executing actions")
def roll(group, batch, grace, auto_approve):
    """Roll an elastigroup.

    GROUP is elastigroup name, alias or regex.
    """
    action(action="roll", target=group, batch=batch, grace=grace, auto_approve=auto_approve)


@click.command()
@click.argument("group")
@click.option("-p", "--processes", multiple=True, default=[], help="Processes to suspend")
@click.option("-y", "--auto-approve", is_flag=True, default=False, help="Skip interactive approval before executing actions")
def suspend(group, processes, auto_approve):
    """Suspend a process in an elastigroup.

    GROUP is elastigroup name, alias or regex.
    """
    action(action="suspend", target=group, processes=processes, auto_approve=auto_approve)


@click.command()
@click.argument("group")
@click.option("-p", "--processes", multiple=True, default=[], help="Processes to unsuspend")
@click.option("-y", "--auto-approve", is_flag=True, default=False, help="Skip interactive approval before executing actions")
def unsuspend(group, processes, auto_approve):
    """Unsuspend a process in an elastigroup.

    GROUP is elastigroup name, alias or regex.
    """
    action(action="unsuspend", target=group, processes=processes, auto_approve=auto_approve)


@click.command()
@click.argument("kind")
@click.argument("group")
@click.option("-a", "--amount", default="10%", help="How many instances to add or remove; amount or percentage")
@click.option("-y", "--auto-approve", is_flag=True, default=False, help="Skip interactive approval before executing actions")
def scale(kind, group, amount, auto_approve):
    """Scale an elastigroup up or down.

    KIND is the scaling direction: up or down.
    GROUP is elastigroup name, alias or regex.
    """
    action(action=f"{kind}scale", target=group, amount=amount, auto_approve=auto_approve)


main.add_command(version)
main.add_command(run)
main.add_command(status)
main.add_command(roll)
main.add_command(suspend)
main.add_command(unsuspend)
main.add_command(scale)


def action(action, target, auto_approve, **kwargs):
    console.print(f"[bold]Spot CLI version {spotcli.__version__}")
    config = spotcli.configuration.load()
    targets = spotcli.tasks.TargetList(config.providers["spot"], config.aliases, [target])
    task = spotcli.tasks.Task(kind=action, targets=targets, **kwargs)
    console.print("\n")
    table = rich.table.Table(title=f"Going to [bold]{task.kind}[/] these elastigroups:")
    table.add_column("ID", justify="center", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Instances", style="green")
    for target in task.targets:
        table.add_row(target.id, target.name, str(target.capacity["target"]))
    console.print(table)
    console.print("\n")
    auto_approve or rich.prompt.Confirm.ask("Continue?") or sys.exit(1)
    t_start = time.time()
    task.run()
    t_end = time.time()
    duration = t_end - t_start
    console.print(f"\n[bold green]Task run complete! Ran 1 task in {duration:.2f} seconds.")


if __name__ == "__main__":
    main()