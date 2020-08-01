""" CLI to create the S3 Sink connector
https://docs.confluent.io/current/connect/kafka-connect-s3
"""

__all__ = ["create_s3_sink"]

import json
import time
from typing import List

import click

from kafkaconnect.config import Config
from kafkaconnect.connect import Connect
from kafkaconnect.s3_sink.config import S3Config
from kafkaconnect.topics import Topic


@click.command("s3-sink")
@click.argument("topiclist", nargs=-1, required=False)
@click.option(
    "-n",
    "--name",
    "name",
    required=False,
    default=S3Config.name,
    show_default=True,
    help=(
        "Name of the connector. Alternatively set via the "
        "$KAFKA_CONNECT_NAME env var."
    ),
)
@click.option(
    "-b",
    "--bucket-name",
    "s3_bucket_name",
    required=False,
    default="",  # S3Config.s3_bucket_name,
    show_default=True,
    help=(
        "s3 bucket name. Must exist already. Alternatively set via the "
        "$KAFKA_CONNECT_S3_BUCKECT_NAME env var."
    ),
)
@click.option(
    "-r",
    "--region",
    "s3_region",
    required=False,
    default=S3Config.s3_region,
    show_default=True,
    help=(
        "s3 region.Alternatively set via the $KAFKA_CONNECT_S3_REGION env var."
    ),
)
@click.option(
    "-d",
    "--topics_dir",
    "topics_dir",
    required=False,
    default=S3Config.topics_dir,
    show_default=True,
    help=(
        "Top level directory to store the data ingested from Kafka. "
        "Alternatively set via the $KAFKA_CONNECT_TOPICS_DIR env var."
    ),
)
@click.option(
    "--flush_size",
    "flush_size",
    required=False,
    default=S3Config.flush_size,
    show_default=True,
    help=(
        "Number of records written to store before invoking file commits."
        "Alternatively set via the $KAFKA_CONNECT_S3_FLUSH_SIZE env var. "
        "Use '-' for unauthenticated users."
    ),
)
@click.option(
    "--rotate_interval_ms",
    "rotate_interval_ms",
    required=False,
    default=S3Config.rotate_interval_ms,
    show_default=True,
    help=(
        "The time interval in milliseconds to invoke file commits. "
        "Alternatively set via the $KAFKA_CONNECT_INFLUXDB_USERNAME env var. "
        "Use '-' for unauthenticated users."
    ),
)
@click.option(
    "-p",
    "--partition_duration_ms",
    "partition_duration_ms",
    required=False,
    default=S3Config.partition_duration_ms,
    show_default=True,
    help=(
        "The duration of a partition in milliseconds used by "
        "TimeBasedPartitioner. Alternatively set via the "
        "$KAFKA_CONNECT_INFLUXDB_PASSWORD env var."
    ),
)
@click.option(
    "-t",
    "--tasks-max",
    "tasks_max",
    required=False,
    default=S3Config.tasks_max,
    show_default=True,
    help=(
        "Number of Kafka Connect tasks. Alternatively set via the "
        "$KAFKA_CONNECT_TASKS_MAX env var."
    ),
)
@click.option(
    "--topic-regex",
    "topic_regex",
    required=False,
    default=Config.topic_regex,
    show_default=True,
    help=(
        "Regex for selecting topics. Alternatively set via the "
        "$KAFKA_CONNECT_TOPIC_REGEX env var."
    ),
)
@click.option(
    "--dry-run",
    is_flag=True,
    help=(
        "Show the InfluxDB Sink Connector configuration but do not create "
        "the connector."
    ),
)
@click.option(
    "--auto-update",
    is_flag=True,
    help=(
        "Check for new topics and update the connector. See also the "
        "--check-interval option."
    ),
)
@click.option(
    "-v",
    "--validate",
    is_flag=True,
    help="Validate the connector configuration before creating.",
)
@click.option(
    "-c",
    "--check-interval",
    "check_interval",
    required=False,
    default=Config.check_interval,
    show_default=True,
    help=(
        "The interval, in milliseconds, to check for new topics and update"
        "the connector."
    ),
)
@click.option(
    "-e",
    "--excluded_topics",
    "excluded_topics",
    required=False,
    default=Config.excluded_topics,
    show_default=True,
    help=(
        "Comma separated list of topics to exclude from "
        "selection. Alternatively set via the "
        "$KAFKA_CONNECT_EXCLUDED_TOPICS env var."
    ),
)
@click.option(
    "--locale",
    "locale",
    required=False,
    default=S3Config.locale,
    show_default=True,
    help="The locale to use when partitioning with TimeBasedPartitioner.",
)
@click.option(
    "--timezone",
    "timezone",
    required=False,
    default=S3Config.timezone,
    show_default=True,
    help="The timezone to use when partitioning with TimeBasedPartitioner.",
)
@click.option(
    "--timestamp_extractor",
    "timestamp_extractor",
    required=False,
    default=S3Config.timestamp_extractor,
    show_default=True,
    help=(
        "The extractor determines how to obtain a timestamp from each record. "
        "Values can be Wallclock to use the system time when "
        "the record is processed, Record to use the timestamp of the "
        "Kafka record denoting when it was produced or stored by the broker, "
        "RecordField to extract the timestamp from one of the fields in the "
        "record’s value as specified by the timestamp_field configuration "
        "property."
    ),
)
@click.option(
    "--timestamp_field",
    "timestamp_field",
    required=False,
    default=S3Config.timestamp_field,
    show_default=True,
    help=(
        "The record field to be used as timestamp by the timestamp extractor."
    ),
)
@click.pass_context
def create_s3_sink(
    ctx: click.Context,
    topiclist: tuple,
    name: str,
    s3_bucket_name: str,
    s3_region: str,
    topics_dir: str,
    flush_size: int,
    rotate_interval_ms: int,
    partition_duration_ms: int,
    tasks_max: int,
    topic_regex: str,
    dry_run: bool,
    auto_update: bool,
    validate: bool,
    check_interval: int,
    excluded_topics: str,
    locale: str,
    timezone: str,
    timestamp_extractor: str,
    timestamp_field: str,
) -> int:
    """Create an instance of the S3 Sink connector.

    A list of topics can be specified using the TOPICLIST argument.
    If not, topics are discovered from Kafka. Use the --topic-regex and
    --excluded_topics options to help in selecting the topics
    that you want to write to S3. To check for new topics and update
    the connector configuration use the
    --auto-update and --check-interval options.
    """
    # Connector configuration
    s3config = S3Config(
        name=name,
        s3_bucket_name=s3_bucket_name,
        s3_region=s3_region,
        topics_dir=topics_dir,
        flush_size=flush_size,
        rotate_interval_ms=rotate_interval_ms,
        partition_duration_ms=partition_duration_ms,
        tasks_max=tasks_max,
        locale=locale,
        timezone=timezone,
        timestamp_extractor=timestamp_extractor,
        timestamp_field=timestamp_field,
    )
    if ctx.parent:
        config = ctx.parent.obj["config"]
    # The variadic argument is a tuple
    topics: List[str] = list(topiclist)
    if not topics:
        click.echo("Discoverying Kafka topics...")
        topics = Topic(config.broker_url, topic_regex, excluded_topics).names
        n = 0 if not topics else len(topics)
        click.echo(f"Found {n} topics.")
    connect = Connect(connect_url=config.connect_url)
    if topics:
        s3config.update_topics(topics)
        # --validate option
        if validate:
            click.echo(
                connect.validate(
                    name=s3config.connector_class,
                    connect_config=s3config.asjson(),
                )
            )
            return 0
        # --dry-run option returns the connector configuration
        if dry_run:
            click.echo(s3config.asjson())
            return 0
        # Validate configuration before creating the connector
        validation = connect.validate(
            name=s3config.connector_class, connect_config=s3config.asjson(),
        )
        try:
            error_count = json.loads(validation)["error_count"]
            click.echo(f"Validation returned {error_count} error(s).")
            if error_count > 0:
                click.echo(
                    "Use the --validate option to return the validation "
                    "results."
                )
            return 0
        except Exception:
            click.echo(validation)
            return 1
        click.echo(f"Uploading {name} connector configuration...")
        connect.create_or_update(name=name, connect_config=s3config.asjson())
    if auto_update:
        while True:
            time.sleep(int(check_interval) / 1000)
            try:
                # Current list of topics from Kafka
                current_topics = Topic(
                    config.broker_url, topic_regex, excluded_topics
                ).names
                new_topics = list(set(current_topics) - set(topics))
                if new_topics:
                    click.echo("Found new topics, updating the connector...")
                    s3config.update_topics(current_topics)
                    connect.create_or_update(
                        name=name, connect_config=s3config.asjson()
                    )
                    topics = current_topics
            except KeyboardInterrupt:
                raise click.ClickException("Interruped.")
    return 0
