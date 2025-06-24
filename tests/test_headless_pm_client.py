#!/usr/bin/env python3
"""
Comprehensive test suite for Headless PM Client
Tests all API endpoints using real API calls with parallel processing
No mocking - creates real records and cleans them up after testing
"""

import os
import sys
import time
import unittest
import uuid
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Set
import requests
from urllib.parse import urljoin
from pathlib import Path

# Add parent directory to path to import the client
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from headless_pm_client import HeadlessPMClient, load_env_file


def TestableHeadlessPMClient(base_url=None, api_key=None):
    """Factory function that returns a testable client that raises exceptions instead of exiting"""
    
    class _TestableClient(HeadlessPMClient):
        def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
            """Make HTTP request to API - raises exceptions instead of exiting"""
            url = urljoin(self.base_url, path)
            kwargs.setdefault("headers", {}).update(self.headers)
            
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
    
    return _TestableClient(base_url, api_key)


class TestHeadlessPMClient(unittest.TestCase):
    """Test suite for Headless PM Client with parallel execution"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        # Load environment variables
        load_env_file()
        
        # Initialize client
        cls.client = TestableHeadlessPMClient()
        
        # Generate unique test run ID to avoid conflicts
        cls.test_run_id = str(uuid.uuid4())[:8]
        
        # PM agent for administrative operations
        cls.pm_agent_id = f"test_pm_{cls.test_run_id}"
        
        # Track all created resources for cleanup
        cls.created_agents: Set[str] = set()
        cls.created_epics: Set[int] = set()
        cls.created_features: Set[int] = set()
        cls.created_tasks: Set[int] = set()
        cls.created_documents: Set[int] = set()
        cls.created_services: Set[str] = set()
        cls.created_mentions: Set[int] = set()
        
        # Register PM agent
        try:
            result = cls.client.register_agent(
                agent_id=cls.pm_agent_id,
                role="pm",
                level="principal",
                connection_type="client"
            )
            cls.created_agents.add(cls.pm_agent_id)
            print(f"✓ Registered PM agent: {cls.pm_agent_id}")
        except Exception as e:
            print(f"Failed to register PM agent: {e}")
            raise
    
    @classmethod
    def tearDownClass(cls):
        """Clean up all created resources"""
        print("\nCleaning up test data...")
        
        # Delete in reverse order of dependencies
        cleanup_tasks = []
        
        # 1. Unregister services
        for service_name in cls.created_services:
            cleanup_tasks.append(("service", service_name))
        
        # 2. Delete documents (will cascade delete mentions)
        for doc_id in cls.created_documents:
            cleanup_tasks.append(("document", doc_id))
        
        # 3. Delete tasks
        for task_id in cls.created_tasks:
            cleanup_tasks.append(("task", task_id))
        
        # 4. Delete features
        for feature_id in cls.created_features:
            cleanup_tasks.append(("feature", feature_id))
        
        # 5. Delete epics
        for epic_id in cls.created_epics:
            cleanup_tasks.append(("epic", epic_id))
        
        # 6. Delete agents (except PM agent)
        for agent_id in cls.created_agents:
            if agent_id != cls.pm_agent_id:
                cleanup_tasks.append(("agent", agent_id))
        
        # Execute cleanup in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for resource_type, resource_id in cleanup_tasks:
                future = executor.submit(cls._cleanup_resource, resource_type, resource_id)
                futures.append(future)
            
            # Wait for all cleanup tasks
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Cleanup error: {e}")
        
        # Finally, delete PM agent
        try:
            cls.client.delete_agent(cls.pm_agent_id, cls.pm_agent_id)
            print(f"✓ Deleted PM agent: {cls.pm_agent_id}")
        except Exception as e:
            # It's expected that PM agent can't delete itself
            if "Cannot delete your own agent record" in str(e):
                print(f"✓ PM agent {cls.pm_agent_id} remains (cannot self-delete)")
            else:
                print(f"Failed to delete PM agent: {e}")
    
    @classmethod
    def _cleanup_resource(cls, resource_type: str, resource_id: Any):
        """Clean up a single resource"""
        try:
            if resource_type == "service":
                cls.client.unregister_service(resource_id, cls.pm_agent_id)
            elif resource_type == "document":
                cls.client.delete_document(resource_id)
            elif resource_type == "task":
                cls.client.delete_task(resource_id, cls.pm_agent_id)
            elif resource_type == "feature":
                cls.client.delete_feature(resource_id, cls.pm_agent_id)
            elif resource_type == "epic":
                cls.client.delete_epic(resource_id, cls.pm_agent_id)
            elif resource_type == "agent":
                cls.client.delete_agent(resource_id, cls.pm_agent_id)
            print(f"✓ Deleted {resource_type}: {resource_id}")
        except Exception as e:
            print(f"✗ Failed to delete {resource_type} {resource_id}: {e}")
    
    def _generate_unique_id(self, prefix: str) -> str:
        """Generate unique ID for test resources"""
        return f"{prefix}_{self.test_run_id}_{uuid.uuid4().hex[:6]}"
    
    # Test Methods - Agent Management
    
    def test_agent_management(self):
        """Test agent registration, listing, and deletion"""
        print("\n=== Testing Agent Management ===")
        
        # Create multiple agents in parallel
        agent_configs = [
            ("frontend_dev", "senior"),
            ("backend_dev", "junior"),
            ("qa", "principal"),
            ("architect", "senior")
        ]
        
        created_in_test = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            
            # Register agents in parallel
            for role, level in agent_configs:
                agent_id = self._generate_unique_id(f"test_{role}")
                future = executor.submit(
                    self.client.register_agent,
                    agent_id=agent_id,
                    role=role,
                    level=level,
                    connection_type="client"
                )
                futures[future] = agent_id
            
            # Collect results
            for future in as_completed(futures):
                agent_id = futures[future]
                try:
                    result = future.result()
                    self.created_agents.add(agent_id)
                    created_in_test.append(agent_id)
                    # Check if agent_id is in the response (either directly or in nested agent object)
                    if "agent_id" in result:
                        self.assertEqual(result["agent_id"], agent_id)
                    elif "agent" in result and "agent_id" in result["agent"]:
                        self.assertEqual(result["agent"]["agent_id"], agent_id)
                    else:
                        self.fail(f"agent_id not found in response: {result}")
                    print(f"✓ Registered agent: {agent_id}")
                except Exception as e:
                    self.fail(f"Failed to register agent {agent_id}: {e}")
        
        # List all agents
        agents = self.client.list_agents()
        self.assertIsInstance(agents, list)
        agent_ids = [a["agent_id"] for a in agents]
        
        # Verify our agents are in the list
        for agent_id in created_in_test:
            self.assertIn(agent_id, agent_ids)
        
        print(f"✓ Listed {len(agents)} agents")
        
        # Test deletion (pick one agent)
        if created_in_test:
            agent_to_delete = created_in_test[0]
            result = self.client.delete_agent(agent_to_delete, self.pm_agent_id)
            self.assertIn("success", str(result).lower())
            self.created_agents.discard(agent_to_delete)
            print(f"✓ Deleted agent: {agent_to_delete}")
    
    def test_project_structure(self):
        """Test epic and feature management"""
        print("\n=== Testing Project Structure (Epics/Features) ===")
        
        # Create epics
        epic_configs = [
            ("User Authentication", "Implement complete auth system"),
            ("Dashboard Redesign", "Modernize the dashboard UI"),
            ("API Optimization", "Improve API performance")
        ]
        
        created_epics = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            
            for name, description in epic_configs:
                epic_name = f"{name} {self.test_run_id}"
                future = executor.submit(
                    self.client.create_epic,
                    name=epic_name,
                    description=description,
                    agent_id=self.pm_agent_id
                )
                futures[future] = epic_name
            
            for future in as_completed(futures):
                epic_name = futures[future]
                try:
                    result = future.result()
                    epic_id = result["id"]
                    self.created_epics.add(epic_id)
                    created_epics.append((epic_id, epic_name))
                    print(f"✓ Created epic: {epic_name} (ID: {epic_id})")
                except Exception as e:
                    self.fail(f"Failed to create epic {epic_name}: {e}")
        
        # List epics
        epics = self.client.list_epics()
        self.assertIsInstance(epics, list)
        print(f"✓ Listed {len(epics)} epics")
        
        # Create features for the first epic
        if created_epics:
            epic_id, epic_name = created_epics[0]
            feature_configs = [
                ("Login Flow", "Implement login with 2FA"),
                ("Password Reset", "Add password reset functionality"),
                ("Session Management", "Handle user sessions")
            ]
            
            created_features = []
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {}
                
                for name, description in feature_configs:
                    feature_name = f"{name} {self.test_run_id}"
                    future = executor.submit(
                        self.client.create_feature,
                        epic_id=epic_id,
                        name=feature_name,
                        description=description,
                        agent_id=self.pm_agent_id
                    )
                    futures[future] = feature_name
                
                for future in as_completed(futures):
                    feature_name = futures[future]
                    try:
                        result = future.result()
                        feature_id = result["id"]
                        self.created_features.add(feature_id)
                        created_features.append((feature_id, feature_name))
                        print(f"✓ Created feature: {feature_name} (ID: {feature_id})")
                    except Exception as e:
                        self.fail(f"Failed to create feature {feature_name}: {e}")
            
            # List features for epic
            features = self.client.list_features(epic_id)
            self.assertIsInstance(features, list)
            self.assertEqual(len(features), len(feature_configs))
            print(f"✓ Listed {len(features)} features for epic {epic_id}")
    
    def test_task_lifecycle(self):
        """Test complete task lifecycle with parallel operations"""
        print("\n=== Testing Task Lifecycle ===")
        
        # First create an epic and feature
        epic_result = self.client.create_epic(
            name=f"Task Test Epic {self.test_run_id}",
            description="Epic for task testing",
            agent_id=self.pm_agent_id
        )
        epic_id = epic_result["id"]
        self.created_epics.add(epic_id)
        
        feature_result = self.client.create_feature(
            epic_id=epic_id,
            name=f"Task Test Feature {self.test_run_id}",
            description="Feature for task testing",
            agent_id=self.pm_agent_id
        )
        feature_id = feature_result["id"]
        self.created_features.add(feature_id)
        
        # Create test agent for task assignment
        dev_agent_id = self._generate_unique_id("test_dev")
        self.client.register_agent(
            agent_id=dev_agent_id,
            role="backend_dev",
            level="senior",
            connection_type="client"
        )
        self.created_agents.add(dev_agent_id)
        
        # Create multiple tasks in parallel
        task_configs = [
            ("Implement API endpoint", "Create REST endpoint", "backend_dev", "senior", "minor"),
            ("Add database schema", "Design and implement schema", "backend_dev", "senior", "major"),
            ("Write unit tests", "Add comprehensive tests", "backend_dev", "junior", "minor"),
            ("Add documentation", "Document the new feature", "backend_dev", "junior", "minor")
        ]
        
        created_tasks = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            
            for title, desc, role, difficulty, complexity in task_configs:
                task_title = f"{title} {self.test_run_id}"
                branch = f"feature/{self._generate_unique_id('branch')}"
                future = executor.submit(
                    self.client.create_task,
                    feature_id=feature_id,
                    title=task_title,
                    description=desc,
                    target_role=role,
                    difficulty=difficulty,
                    complexity=complexity,
                    branch=branch,
                    agent_id=self.pm_agent_id
                )
                futures[future] = task_title
            
            for future in as_completed(futures):
                task_title = futures[future]
                try:
                    result = future.result()
                    task_id = result["id"]
                    self.created_tasks.add(task_id)
                    created_tasks.append((task_id, task_title))
                    print(f"✓ Created task: {task_title} (ID: {task_id})")
                except Exception as e:
                    self.fail(f"Failed to create task {task_title}: {e}")
        
        # Test task workflow with one task
        if created_tasks:
            task_id, task_title = created_tasks[0]
            
            # Get next task
            next_task = self.client.get_next_task(role="backend_dev", level="senior")
            if next_task:
                print(f"✓ Got next task: {next_task.get('title', 'Unknown')}")
                
                # Lock task
                lock_result = self.client.lock_task(task_id, dev_agent_id)
                print(f"✓ Locked task {task_id}")
                
                # Update status through workflow
                statuses = ["under_work", "dev_done", "committed"]
                for status in statuses:
                    result = self.client.update_task_status(
                        task_id=task_id,
                        status=status,
                        agent_id=dev_agent_id,
                        notes=f"Updated to {status} by test"
                    )
                    print(f"✓ Updated task status to: {status}")
                    time.sleep(0.1)  # Small delay between status updates
                
                # Add comment with mention
                comment = f"Task completed successfully. @{self.pm_agent_id} please review."
                self.client.add_task_comment(task_id, comment, dev_agent_id)
                print(f"✓ Added comment with mention to task {task_id}")
    
    def test_document_system(self):
        """Test document creation, listing, and mention detection"""
        print("\n=== Testing Document System ===")
        
        # Create test agent to mention
        mentioned_agent_id = self._generate_unique_id("test_mentioned")
        self.client.register_agent(
            agent_id=mentioned_agent_id,
            role="qa",
            level="senior",
            connection_type="client"
        )
        self.created_agents.add(mentioned_agent_id)
        
        # Document configurations
        doc_configs = [
            ("standup", "Daily Standup", f"Working on testing. @{mentioned_agent_id} need your input."),
            ("critical_issue", "Database Connection Error", f"Production DB is down! @{self.pm_agent_id} urgent!"),
            ("update", "Feature Complete", f"Finished implementation. @{mentioned_agent_id} ready for QA."),
            ("service_status", "API Status", "All services operational. No issues to report.")
        ]
        
        created_docs = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            
            for doc_type, title, content in doc_configs:
                doc_title = f"{title} {self.test_run_id}"
                future = executor.submit(
                    self.client.create_document,
                    doc_type=doc_type,
                    title=doc_title,
                    content=content,
                    author_id=self.pm_agent_id
                )
                futures[future] = (doc_type, doc_title)
            
            for future in as_completed(futures):
                doc_type, doc_title = futures[future]
                try:
                    result = future.result()
                    doc_id = result["id"]
                    self.created_documents.add(doc_id)
                    created_docs.append((doc_id, doc_title))
                    
                    # Track mention IDs if present
                    # Note: mentions in create response are just agent_ids, not mention objects
                    
                    print(f"✓ Created {doc_type} document: {doc_title} (ID: {doc_id})")
                except Exception as e:
                    self.fail(f"Failed to create document {doc_title}: {e}")
        
        # List documents
        docs = self.client.list_documents(limit=100)
        self.assertIsInstance(docs, list)
        print(f"✓ Listed {len(docs)} documents")
        
        # Get specific document
        if created_docs:
            doc_id, doc_title = created_docs[0]
            doc = self.client.get_document(doc_id)
            self.assertEqual(doc["id"], doc_id)
            print(f"✓ Retrieved document {doc_id}")
            
            # Update document
            new_content = f"Updated content. @{mentioned_agent_id} please check this."
            self.client.update_document(
                document_id=doc_id,
                content=new_content
            )
            print(f"✓ Updated document {doc_id}")
        
        # Check mentions for mentioned agent
        mentions = self.client.get_mentions(mentioned_agent_id, unread_only=True)
        self.assertIsInstance(mentions, list)
        self.assertGreater(len(mentions), 0, "Should have at least one mention")
        print(f"✓ Found {len(mentions)} mentions for {mentioned_agent_id}")
        
        # Mark mention as read
        if mentions:
            mention_id = mentions[0]["id"]
            self.client.mark_mention_read(mention_id, mentioned_agent_id)
            print(f"✓ Marked mention {mention_id} as read")
    
    def test_service_registry(self):
        """Test service registration and management"""
        print("\n=== Testing Service Registry ===")
        
        # Service configurations
        service_configs = [
            ("api-gateway", "http://localhost:8080/health", 8080),
            ("auth-service", "http://localhost:8081/health", 8081),
            ("data-service", "http://localhost:8082/health", 8082),
            ("worker-service", "http://localhost:8083/health", 8083)
        ]
        
        created_services = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            
            for name, ping_url, port in service_configs:
                service_name = f"{name}-{self.test_run_id}"
                future = executor.submit(
                    self.client.register_service,
                    service_name=service_name,
                    ping_url=ping_url,
                    agent_id=self.pm_agent_id,
                    port=port,
                    status="up",
                    meta_data={"version": "1.0.0", "test": True}
                )
                futures[future] = service_name
            
            for future in as_completed(futures):
                service_name = futures[future]
                try:
                    result = future.result()
                    self.created_services.add(service_name)
                    created_services.append(service_name)
                    print(f"✓ Registered service: {service_name}")
                except Exception as e:
                    self.fail(f"Failed to register service {service_name}: {e}")
        
        # List services
        services = self.client.list_services()
        self.assertIsInstance(services, list)
        print(f"✓ Listed {len(services)} services")
        
        # Send heartbeats in parallel
        if created_services:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {}
                
                for service_name in created_services[:2]:  # Test with first 2 services
                    future = executor.submit(
                        self.client.service_heartbeat,
                        service_name=service_name,
                        agent_id=self.pm_agent_id
                    )
                    futures[future] = service_name
                
                for future in as_completed(futures):
                    service_name = futures[future]
                    try:
                        result = future.result()
                        print(f"✓ Sent heartbeat for service: {service_name}")
                    except Exception as e:
                        print(f"✗ Failed to send heartbeat for {service_name}: {e}")
    
    def test_changes_and_changelog(self):
        """Test polling for changes and changelog"""
        print("\n=== Testing Changes and Changelog ===")
        
        # Get current time
        start_time = datetime.utcnow()
        
        # Create some activity
        doc_result = self.client.create_document(
            doc_type="update",
            title=f"Test Update {self.test_run_id}",
            content="Creating activity for change detection",
            author_id=self.pm_agent_id
        )
        self.created_documents.add(doc_result["id"])
        
        # Wait a moment
        time.sleep(1)
        
        # Poll for changes
        since_time = start_time.isoformat() + "Z"
        changes = self.client.get_changes(since=since_time, agent_id=self.pm_agent_id)
        self.assertIsInstance(changes, dict)
        print(f"✓ Polled changes since {since_time}")
        
        # Get changelog
        changelog = self.client.get_changelog(limit=10)
        self.assertIsInstance(changelog, list)
        print(f"✓ Retrieved changelog with {len(changelog)} entries")
    
    def test_context_endpoint(self):
        """Test project context retrieval"""
        print("\n=== Testing Context Endpoint ===")
        
        context = self.client.get_context()
        self.assertIsInstance(context, dict)
        self.assertIn("project_name", context)
        self.assertIn("shared_path", context)
        self.assertIn("database_type", context)
        print(f"✓ Retrieved project context")
        print(f"  - Project Name: {context.get('project_name', 'N/A')}")
        print(f"  - Shared Path: {context.get('shared_path', 'N/A')}")
        print(f"  - Database Type: {context.get('database_type', 'N/A')}")
    
    def test_parallel_stress_test(self):
        """Stress test with many parallel operations"""
        print("\n=== Running Parallel Stress Test ===")
        
        operations = []
        
        # Queue up various operations
        for i in range(10):
            operations.append(("list_agents", None))
            operations.append(("list_services", None))
            operations.append(("list_epics", None))
            operations.append(("get_changelog", {"limit": 5}))
        
        success_count = 0
        error_count = 0
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {}
            
            for op_name, params in operations:
                if op_name == "list_agents":
                    future = executor.submit(self.client.list_agents)
                elif op_name == "list_services":
                    future = executor.submit(self.client.list_services)
                elif op_name == "list_epics":
                    future = executor.submit(self.client.list_epics)
                elif op_name == "get_changelog":
                    future = executor.submit(self.client.get_changelog, **params)
                
                futures[future] = op_name
            
            for future in as_completed(futures):
                op_name = futures[future]
                try:
                    result = future.result()
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"✗ Error in {op_name}: {e}")
        
        print(f"✓ Stress test complete: {success_count} successful, {error_count} errors")
        self.assertEqual(error_count, 0, "All operations should succeed")


def run_tests():
    """Run all tests with detailed output"""
    print("=" * 80)
    print("Headless PM Client Test Suite")
    print("=" * 80)
    print(f"Test started at: {datetime.now()}")
    print(f"API URL: {os.getenv('HEADLESS_PM_URL', 'http://localhost:6969')}")
    print("=" * 80)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHeadlessPMClient)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    print(f"Test completed at: {datetime.now()}")
    print("=" * 80)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)