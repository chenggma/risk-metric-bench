import unittest
import xml.etree.ElementTree as ET

from bench.scenario import CONFIG, EDGES, NODES, ROUTES


class TestScenarioXml(unittest.TestCase):
    def test_nodes_wellformed(self):
        root = ET.fromstring(NODES)
        self.assertEqual(len(root.findall("node")), 5)

    def test_edges_wellformed_and_prioritized(self):
        root = ET.fromstring(EDGES)
        edges = root.findall("edge")
        self.assertEqual(len(edges), 8)
        major = [e for e in edges if e.get("priority") == "10"]
        minor = [e for e in edges if e.get("priority") == "2"]
        self.assertEqual(len(major), 4)
        self.assertEqual(len(minor), 4)

    def test_routes_formatting(self):
        xml = ROUTES.format(
            end=300,
            major_flow=700,
            minor_flow=500,
            ignore_prob=0.30,
            major_blind_prob=0.50,
        )
        root = ET.fromstring(xml)
        minor = [v for v in root.findall("vType") if v.get("id") == "minor"]
        self.assertEqual(minor[0].get("jmIgnoreFoeProb"), "0.3")
        major = [v for v in root.findall("vType") if v.get("id") == "major"]
        self.assertEqual(major[0].get("jmIgnoreJunctionFoeProb"), "0.5")
        flows = root.findall("flow")
        self.assertEqual(len(flows), 4)
        self.assertTrue(all(f.get("end") == "300" for f in flows))

    def test_config_formatting(self):
        xml = CONFIG.format(end=300, seed=7)
        root = ET.fromstring(xml)
        seed = root.find("random_number/seed")
        self.assertEqual(seed.get("value"), "7")
        col = root.find("processing/collision.action")
        self.assertEqual(col.get("value"), "warn")


if __name__ == "__main__":
    unittest.main()
