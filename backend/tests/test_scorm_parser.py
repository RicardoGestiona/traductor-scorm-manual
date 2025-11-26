"""
Tests para ScormParser service.

Filepath: backend/tests/test_scorm_parser.py
Feature alignment: STORY-005 - Parser de SCORM 1.2
"""

import pytest
from lxml import etree
from app.services.scorm_parser import ScormParser


class TestScormParser:
    """Tests para ScormParser."""

    def setup_method(self):
        """Setup que se ejecuta antes de cada test."""
        self.parser = ScormParser()

    def test_detect_scorm_12_version(self):
        """Test: Detectar SCORM 1.2 desde manifest."""
        manifest_xml = """<?xml version="1.0"?>
        <manifest identifier="SCORM12Example" version="1.0"
                  schemaversion="1.2"
                  xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2">
            <metadata/>
            <organizations/>
            <resources/>
        </manifest>
        """
        root = etree.fromstring(manifest_xml.encode())
        version = self.parser._detect_scorm_version(root)

        assert version == "1.2"

    def test_detect_scorm_2004_version(self):
        """Test: Detectar SCORM 2004 desde manifest."""
        manifest_xml = """<?xml version="1.0"?>
        <manifest identifier="SCORM2004Example" version="1.0"
                  schemaversion="2004 4th Edition"
                  xmlns="http://www.imsglobal.org/xsd/imscp_v1p1">
            <metadata/>
            <organizations/>
            <resources/>
        </manifest>
        """
        root = etree.fromstring(manifest_xml.encode())
        version = self.parser._detect_scorm_version(root)

        assert version == "2004"

    def test_parse_metadata(self):
        """Test: Parsear metadata básico."""
        manifest_xml = """<?xml version="1.0"?>
        <manifest xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2">
            <metadata>
                <schema>ADL SCORM</schema>
                <schemaversion>1.2</schemaversion>
            </metadata>
        </manifest>
        """
        root = etree.fromstring(manifest_xml.encode())
        metadata = self.parser._parse_metadata(root)

        assert metadata is not None
        # Metadata básico sin title/description debe crear objeto vacío
        assert metadata.title is None

    def test_parse_organizations_with_single_item(self):
        """Test: Parsear organizaciones con un item."""
        manifest_xml = """<?xml version="1.0"?>
        <manifest xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2">
            <organizations default="ORG-001">
                <organization identifier="ORG-001">
                    <title>Curso de Ejemplo</title>
                    <item identifier="ITEM-001" identifierref="RES-001">
                        <title>Lección 1</title>
                    </item>
                </organization>
            </organizations>
        </manifest>
        """
        root = etree.fromstring(manifest_xml.encode())
        organizations = self.parser._parse_organizations(root)

        assert len(organizations) == 1
        assert organizations[0].identifier == "ORG-001"
        assert organizations[0].title == "Curso de Ejemplo"
        assert len(organizations[0].items) == 1
        assert organizations[0].items[0].title == "Lección 1"

    def test_parse_resources(self):
        """Test: Parsear recursos."""
        manifest_xml = """<?xml version="1.0"?>
        <manifest xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2">
            <resources>
                <resource identifier="RES-001" type="webcontent" href="index.html">
                    <file href="index.html"/>
                    <file href="styles.css"/>
                </resource>
            </resources>
        </manifest>
        """
        root = etree.fromstring(manifest_xml.encode())
        resources = self.parser._parse_resources(root)

        assert len(resources) == 1
        assert resources[0].identifier == "RES-001"
        assert resources[0].type == "webcontent"
        assert resources[0].href == "index.html"
        assert len(resources[0].files) == 2

    def test_parse_nested_items(self):
        """Test: Parsear items anidados (jerarquía)."""
        manifest_xml = """<?xml version="1.0"?>
        <manifest xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2">
            <organizations>
                <organization identifier="ORG-001">
                    <title>Curso</title>
                    <item identifier="ITEM-001">
                        <title>Módulo 1</title>
                        <item identifier="ITEM-001-1">
                            <title>Lección 1.1</title>
                        </item>
                        <item identifier="ITEM-001-2">
                            <title>Lección 1.2</title>
                        </item>
                    </item>
                </organization>
            </organizations>
        </manifest>
        """
        root = etree.fromstring(manifest_xml.encode())
        organizations = self.parser._parse_organizations(root)

        assert len(organizations) == 1
        assert len(organizations[0].items) == 1
        parent_item = organizations[0].items[0]
        assert parent_item.title == "Módulo 1"
        assert len(parent_item.children) == 2
        assert parent_item.children[0].title == "Lección 1.1"
        assert parent_item.children[1].title == "Lección 1.2"
