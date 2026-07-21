from __future__ import annotations

from configparser import ConfigParser

from sisfact.integrations.base import Connector
from sisfact.integrations.file_connector import FileConnector
from sisfact.integrations.models import DataSource, SourceType
from sisfact.integrations.oracle_connector import OracleConnector
from sisfact.integrations.rest_connector import RestConnector
from sisfact.integrations.soap_connector import SoapConnector
from sisfact.integrations.sqlserver_connector import SqlServerConnector


class ConnectorFactory:
    def __init__(self, config: ConfigParser):
        self.config = config

    def create(self, source: DataSource) -> Connector:
        if source.source_type == SourceType.ORACLE:
            return OracleConnector(source, self.config)
        if source.source_type == SourceType.SQLSERVER:
            return SqlServerConnector(source, self.config)
        if source.source_type == SourceType.REST:
            return RestConnector(source, self.config)
        if source.source_type == SourceType.SOAP:
            return SoapConnector(source, self.config)
        if source.source_type == SourceType.FILE:
            return FileConnector(source, self.config)
        raise ValueError(f"Tipo de fuente no soportado aún: {source.source_type}")
