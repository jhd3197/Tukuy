"""Tests for the XML plugin."""

import json

import pytest

from tukuy.plugins.xml_plugin import (
    XmlPlugin,
    xml_read,
    xml_write,
    xml_xpath,
    xml_validate,
    xml_to_json,
)
from tukuy.safety import SafetyPolicy


# ── Skill tests ───────────────────────────────────────────────────────────


class TestXmlRead:
    def test_read_xml(self, tmp_path):
        p = tmp_path / "data.xml"
        p.write_text(
            '<?xml version="1.0"?>\n<root><name>Alice</name><age>30</age></root>',
            encoding="utf-8",
        )
        result = xml_read.__skill__.invoke(str(p))
        assert result.success is True
        data = result.value["data"]
        assert "root" in data
        assert data["root"]["name"] == "Alice"
        assert data["root"]["age"] == "30"

    def test_read_with_attributes(self, tmp_path):
        p = tmp_path / "data.xml"
        p.write_text(
            '<root><item id="1">hello</item></root>',
            encoding="utf-8",
        )
        result = xml_read.__skill__.invoke(str(p))
        assert result.success is True
        item = result.value["data"]["root"]["item"]
        assert item["@id"] == "1"
        assert item["#text"] == "hello"

    def test_read_nonexistent(self, tmp_path):
        result = xml_read.__skill__.invoke(str(tmp_path / "nope.xml"))
        assert result.success is False


class TestXmlWrite:
    def test_write_xml(self, tmp_path):
        p = tmp_path / "out.xml"
        data = {"name": "Alice", "age": "30"}
        result = xml_write.__skill__.invoke(str(p), data=data, root_tag="person")
        assert result.success is True
        assert result.value["bytes_written"] > 0
        content = p.read_text(encoding="utf-8")
        assert "<person>" in content
        assert "<name>Alice</name>" in content

    def test_write_creates_dirs(self, tmp_path):
        p = tmp_path / "sub" / "dir" / "out.xml"
        xml_write.__skill__.invoke(str(p), data={"x": "1"})
        assert p.exists()

    def test_roundtrip(self, tmp_path):
        p = tmp_path / "rt.xml"
        data = {"name": "Alice", "city": "Lima"}
        xml_write.__skill__.invoke(str(p), data=data, root_tag="person")
        result = xml_read.__skill__.invoke(str(p))
        assert result.success is True
        assert result.value["data"]["person"]["name"] == "Alice"
        assert result.value["data"]["person"]["city"] == "Lima"


class TestXmlXpath:
    def test_xpath_query(self, tmp_path):
        p = tmp_path / "data.xml"
        p.write_text(
            "<root><item>A</item><item>B</item><other>C</other></root>",
            encoding="utf-8",
        )
        result = xml_xpath.__skill__.invoke(str(p), expression=".//item")
        assert result.success is True
        assert result.value["count"] == 2

    def test_xpath_no_match(self, tmp_path):
        p = tmp_path / "data.xml"
        p.write_text("<root><item>A</item></root>", encoding="utf-8")
        result = xml_xpath.__skill__.invoke(str(p), expression=".//missing")
        assert result.success is True
        assert result.value["count"] == 0


class TestXmlValidate:
    def test_valid_xml(self, tmp_path):
        p = tmp_path / "data.xml"
        p.write_text("<root><item>A</item></root>", encoding="utf-8")
        result = xml_validate.__skill__.invoke(str(p))
        assert result.success is True
        assert result.value["valid"] is True
        assert result.value["error"] is None

    def test_invalid_xml(self, tmp_path):
        p = tmp_path / "bad.xml"
        p.write_text("<root><unclosed>", encoding="utf-8")
        result = xml_validate.__skill__.invoke(str(p))
        assert result.success is True
        assert result.value["valid"] is False
        assert result.value["error"] is not None


class TestXmlToJson:
    def test_to_json(self, tmp_path):
        p = tmp_path / "data.xml"
        p.write_text("<root><name>Alice</name></root>", encoding="utf-8")
        result = xml_to_json.__skill__.invoke(str(p))
        assert result.success is True
        parsed = json.loads(result.value["json_string"])
        assert parsed["root"]["name"] == "Alice"

    def test_to_json_nonexistent(self, tmp_path):
        result = xml_to_json.__skill__.invoke(str(tmp_path / "nope.xml"))
        assert result.success is False


# ── Safety policy tests ──────────────────────────────────────────────────


class TestXmlSafety:
    def test_blocked_by_restrictive_policy(self, tmp_path):
        p = tmp_path / "data.xml"
        p.write_text("<root/>", encoding="utf-8")
        policy = SafetyPolicy(allow_filesystem=False)
        result = xml_read.__skill__.invoke(str(p), policy=policy)
        assert result.failed
        assert "filesystem" in result.error.lower()

    def test_allowed_by_permissive_policy(self, tmp_path):
        p = tmp_path / "data.xml"
        p.write_text("<root/>", encoding="utf-8")
        policy = SafetyPolicy.permissive()
        result = xml_read.__skill__.invoke(str(p), policy=policy)
        assert result.success is True

    def test_all_skills_declare_filesystem(self):
        plugin = XmlPlugin()
        for name, sk in plugin.skills.items():
            assert sk.descriptor.requires_filesystem is True, f"{name} missing requires_filesystem"


# ── Plugin registration ──────────────────────────────────────────────────


class TestXmlPlugin:
    def test_plugin_name(self):
        plugin = XmlPlugin()
        assert plugin.name == "xml"

    def test_no_transformers(self):
        plugin = XmlPlugin()
        assert plugin.transformers == {}

    def test_has_all_skills(self):
        plugin = XmlPlugin()
        names = set(plugin.skills.keys())
        assert names == {"xml_read", "xml_write", "xml_xpath", "xml_validate", "xml_to_json"}
