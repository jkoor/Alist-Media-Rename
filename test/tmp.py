import click


def abort_if_false(ctx, param, value):
    if not value:
        print(type(ctx))


@click.command()
@click.option(
    "--yes",
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt="Are you sure you want to drop the db?",
)
def dropdb():
    click.echo("Dropped all tables!")

dropdb()
