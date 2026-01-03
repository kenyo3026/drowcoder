"""
Unit tests for agent tool call pruning behavior.

Tests cover:
- Tool message pruning with keep_last_k_tool_call_contexts parameter
- Tool message content replacement with PRUNED_TOOL_CONTENT placeholder
- Tool call ID matching (no mismatches after pruning)
- Edge cases (keep_all, prune_all, various k values)

Usage:
    # Run tests
    pytest src/drowcoder/tests/test_agent_tool_call_pruning.py -v

    # Or with direct execution
    python -m src.drowcoder.tests.test_agent_tool_call_pruning
"""

import pytest
import sys
from pathlib import Path

# Add src to path (similar to tools/tests pattern)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import from drowcoder
from drowcoder.agent import DrowAgent, AgentRole, PRUNED_TOOL_CONTENT


@pytest.fixture
def agent(tmp_workspace):
    """Create a DrowAgent instance for testing."""
    # Create checkpoint directory inside tmp_workspace
    checkpoint_path = tmp_workspace / "checkpoints" / "test_checkpoint"
    checkpoint_path.mkdir(parents=True, exist_ok=True)

    agent = DrowAgent(
        workspace=str(tmp_workspace),
        checkpoint=str(checkpoint_path),
        keep_last_k_tool_call_contexts=1,
        max_iterations=10,
    )
    agent.init()
    return agent


class TestToolCallPruningBasic:
    """Basic tool call pruning functionality tests."""

    def test_prune_old_tool_messages(self, agent):
        """Test that old tool messages have their content replaced with placeholder."""
        # Setup: Add two tool call groups
        group_1_id = "group_1_abc123"
        group_2_id = "group_2_def456"

        agent.tool_call_group_ids.extend([group_1_id, group_2_id])

        # Group 1: First tool call (will be pruned)
        assistant_msg_1 = {
            "role": AgentRole.ASSISTANT,
            "content": "I will call a tool",
            "tool_calls": [
                {
                    "id": "call_7uTLEjbb2vF4emuT9RLNOOue",
                    "type": "function",
                    "function": {
                        "name": "load",
                        "arguments": '{"file_path": "test.txt"}'
                    }
                }
            ]
        }
        agent.messages.append(assistant_msg_1)

        tool_response_1 = {
            "role": AgentRole.TOOL,
            "tool_call_id": "call_7uTLEjbb2vF4emuT9RLNOOue",
            "tool_call_group_id": group_1_id,
            "content": "File content here",
            "name": "load",
            "arguments": {"file_path": "test.txt"},
            "captured_logs": ""
        }
        agent.messages.append(tool_response_1)

        # Group 2: Second tool call (will be kept)
        assistant_msg_2 = {
            "role": AgentRole.ASSISTANT,
            "content": "I will call another tool",
            "tool_calls": [
                {
                    "id": "call_another_tool_123",
                    "type": "function",
                    "function": {
                        "name": "load",
                        "arguments": '{"file_path": "another.txt"}'
                    }
                }
            ]
        }
        agent.messages.append(assistant_msg_2)

        tool_response_2 = {
            "role": AgentRole.TOOL,
            "tool_call_id": "call_another_tool_123",
            "tool_call_group_id": group_2_id,
            "content": "Another file content",
            "name": "load",
            "arguments": {"file_path": "another.txt"},
            "captured_logs": ""
        }
        agent.messages.append(tool_response_2)

        # Prepare messages with pruning
        prepared_messages = agent._prepare_messages(
            agent.messages,
            last_k_tool_call_group=agent.keep_last_k_tool_call_contexts
        )

        # Verify: Group 1 tool message should be pruned
        group_1_tool_msg = next(
            (msg for msg in prepared_messages
             if msg.get('role') == AgentRole.TOOL
             and msg.get('tool_call_group_id') == group_1_id),
            None
        )
        assert group_1_tool_msg is not None, "Group 1 tool message should still exist"
        assert group_1_tool_msg['content'] == PRUNED_TOOL_CONTENT, \
            "Group 1 tool message content should be replaced with placeholder"

        # Verify: Group 2 tool message should have full content
        group_2_tool_msg = next(
            (msg for msg in prepared_messages
             if msg.get('role') == AgentRole.TOOL
             and msg.get('tool_call_group_id') == group_2_id),
            None
        )
        assert group_2_tool_msg is not None, "Group 2 tool message should exist"
        assert group_2_tool_msg['content'] == "Another file content", \
            "Group 2 tool message should have full content"

    def test_no_tool_call_id_mismatch(self, agent):
        """Test that all tool_call_ids have corresponding tool responses after pruning."""
        # Setup: Add two tool call groups
        group_1_id = "group_1_abc123"
        group_2_id = "group_2_def456"

        agent.tool_call_group_ids.extend([group_1_id, group_2_id])

        # Group 1
        assistant_msg_1 = {
            "role": AgentRole.ASSISTANT,
            "content": "I will call a tool",
            "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "load", "arguments": "{}"}}]
        }
        agent.messages.append(assistant_msg_1)
        agent.messages.append({
            "role": AgentRole.TOOL,
            "tool_call_id": "call_1",
            "tool_call_group_id": group_1_id,
            "content": "Response 1"
        })

        # Group 2
        assistant_msg_2 = {
            "role": AgentRole.ASSISTANT,
            "content": "I will call another tool",
            "tool_calls": [{"id": "call_2", "type": "function", "function": {"name": "load", "arguments": "{}"}}]
        }
        agent.messages.append(assistant_msg_2)
        agent.messages.append({
            "role": AgentRole.TOOL,
            "tool_call_id": "call_2",
            "tool_call_group_id": group_2_id,
            "content": "Response 2"
        })

        # Prepare messages
        prepared_messages = agent._prepare_messages(
            agent.messages,
            last_k_tool_call_group=agent.keep_last_k_tool_call_contexts
        )

        # Collect all tool_call_ids from assistant messages
        tool_call_ids_in_assistant = set()
        for msg in prepared_messages:
            if msg.get('role') == AgentRole.ASSISTANT:
                tool_calls = msg.get('tool_calls', [])
                for tc in tool_calls:
                    tool_call_ids_in_assistant.add(tc.get('id'))

        # Collect all tool_call_ids from tool messages
        tool_call_ids_in_responses = set()
        for msg in prepared_messages:
            if msg.get('role') == AgentRole.TOOL:
                tool_call_id = msg.get('tool_call_id')
                if tool_call_id:
                    tool_call_ids_in_responses.add(tool_call_id)

        # Verify: All assistant tool_call_ids should have corresponding tool responses
        missing_responses = tool_call_ids_in_assistant - tool_call_ids_in_responses
        assert len(missing_responses) == 0, \
            f"Tool call IDs without responses: {missing_responses}"


class TestToolCallPruningEdgeCases:
    """Edge case tests for tool call pruning."""

    def test_keep_all_tool_messages(self, agent):
        """Test that keep_last_k_tool_call_contexts=-1 keeps all tool messages."""
        agent.keep_last_k_tool_call_contexts = -1

        # Setup: Add tool messages
        group_1_id = "group_1"
        group_2_id = "group_2"
        agent.tool_call_group_ids.extend([group_1_id, group_2_id])

        agent.messages.append({
            "role": AgentRole.ASSISTANT,
            "content": "Call tool",
            "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "load", "arguments": "{}"}}]
        })
        agent.messages.append({
            "role": AgentRole.TOOL,
            "tool_call_id": "call_1",
            "tool_call_group_id": group_1_id,
            "content": "Response 1"
        })

        agent.messages.append({
            "role": AgentRole.ASSISTANT,
            "content": "Call another tool",
            "tool_calls": [{"id": "call_2", "type": "function", "function": {"name": "load", "arguments": "{}"}}]
        })
        agent.messages.append({
            "role": AgentRole.TOOL,
            "tool_call_id": "call_2",
            "tool_call_group_id": group_2_id,
            "content": "Response 2"
        })

        # Prepare messages
        prepared_messages = agent._prepare_messages(
            agent.messages,
            last_k_tool_call_group=agent.keep_last_k_tool_call_contexts
        )

        # Verify: All tool messages should have full content
        tool_messages = [msg for msg in prepared_messages if msg.get('role') == AgentRole.TOOL]
        assert len(tool_messages) == 2
        assert all(msg['content'] != PRUNED_TOOL_CONTENT for msg in tool_messages), \
            "All tool messages should have full content when keep_last_k=-1"

    def test_prune_all_tool_messages(self, agent):
        """Test that keep_last_k_tool_call_contexts=0 prunes all tool message content."""
        agent.keep_last_k_tool_call_contexts = 0

        # Setup: Add tool messages
        group_1_id = "group_1"
        agent.tool_call_group_ids.append(group_1_id)

        agent.messages.append({
            "role": AgentRole.ASSISTANT,
            "content": "Call tool",
            "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "load", "arguments": "{}"}}]
        })
        agent.messages.append({
            "role": AgentRole.TOOL,
            "tool_call_id": "call_1",
            "tool_call_group_id": group_1_id,
            "content": "Response 1"
        })

        # Prepare messages
        prepared_messages = agent._prepare_messages(
            agent.messages,
            last_k_tool_call_group=agent.keep_last_k_tool_call_contexts
        )

        # Verify: All tool messages should have pruned content
        tool_messages = [msg for msg in prepared_messages if msg.get('role') == AgentRole.TOOL]
        assert len(tool_messages) == 1
        assert tool_messages[0]['content'] == PRUNED_TOOL_CONTENT, \
            "All tool messages should have pruned content when keep_last_k=0"

    def test_multiple_tool_calls_in_same_group(self, agent):
        """Test pruning behavior with multiple tool calls in the same group."""
        group_1_id = "group_1"
        group_2_id = "group_2"
        agent.tool_call_group_ids.extend([group_1_id, group_2_id])

        # Group 1: Multiple tool calls (will be pruned)
        assistant_msg_1 = {
            "role": AgentRole.ASSISTANT,
            "content": "Call multiple tools",
            "tool_calls": [
                {"id": "call_1a", "type": "function", "function": {"name": "load", "arguments": "{}"}},
                {"id": "call_1b", "type": "function", "function": {"name": "load", "arguments": "{}"}}
            ]
        }
        agent.messages.append(assistant_msg_1)
        agent.messages.append({
            "role": AgentRole.TOOL,
            "tool_call_id": "call_1a",
            "tool_call_group_id": group_1_id,
            "content": "Response 1a"
        })
        agent.messages.append({
            "role": AgentRole.TOOL,
            "tool_call_id": "call_1b",
            "tool_call_group_id": group_1_id,
            "content": "Response 1b"
        })

        # Group 2: Single tool call (will be kept)
        assistant_msg_2 = {
            "role": AgentRole.ASSISTANT,
            "content": "Call another tool",
            "tool_calls": [{"id": "call_2", "type": "function", "function": {"name": "load", "arguments": "{}"}}]
        }
        agent.messages.append(assistant_msg_2)
        agent.messages.append({
            "role": AgentRole.TOOL,
            "tool_call_id": "call_2",
            "tool_call_group_id": group_2_id,
            "content": "Response 2"
        })

        # Prepare messages
        prepared_messages = agent._prepare_messages(
            agent.messages,
            last_k_tool_call_group=agent.keep_last_k_tool_call_contexts
        )

        # Verify: All group 1 tool messages should be pruned
        group_1_tool_messages = [
            msg for msg in prepared_messages
            if msg.get('role') == AgentRole.TOOL
            and msg.get('tool_call_group_id') == group_1_id
        ]
        assert len(group_1_tool_messages) == 2
        assert all(msg['content'] == PRUNED_TOOL_CONTENT for msg in group_1_tool_messages), \
            "All group 1 tool messages should be pruned"

        # Verify: Group 2 tool message should have full content
        group_2_tool_msg = next(
            (msg for msg in prepared_messages
             if msg.get('role') == AgentRole.TOOL
             and msg.get('tool_call_group_id') == group_2_id),
            None
        )
        assert group_2_tool_msg is not None
        assert group_2_tool_msg['content'] == "Response 2", \
            "Group 2 tool message should have full content"

    def test_k_equals_5(self, agent):
        """Test that keep_last_k_tool_call_contexts=5 keeps the last 5 tool call groups."""
        agent.keep_last_k_tool_call_contexts = 5

        # Setup: Create 7 tool call groups
        group_ids = [f"group_{i}" for i in range(1, 8)]  # group_1 to group_7
        agent.tool_call_group_ids.extend(group_ids)

        # Add messages for each group
        for i, group_id in enumerate(group_ids, start=1):
            assistant_msg = {
                "role": AgentRole.ASSISTANT,
                "content": f"Call tool {i}",
                "tool_calls": [{"id": f"call_{i}", "type": "function", "function": {"name": "load", "arguments": "{}"}}]
            }
            agent.messages.append(assistant_msg)

            tool_msg = {
                "role": AgentRole.TOOL,
                "tool_call_id": f"call_{i}",
                "tool_call_group_id": group_id,
                "content": f"Response {i}"
            }
            agent.messages.append(tool_msg)

        # Prepare messages with k=5
        prepared_messages = agent._prepare_messages(
            agent.messages,
            last_k_tool_call_group=agent.keep_last_k_tool_call_contexts
        )

        # Verify: First 2 groups (group_1, group_2) should be pruned
        for i in range(1, 3):  # group_1 and group_2
            group_id = f"group_{i}"
            tool_msg = next(
                (msg for msg in prepared_messages
                 if msg.get('role') == AgentRole.TOOL
                 and msg.get('tool_call_group_id') == group_id),
                None
            )
            assert tool_msg is not None, f"Group {i} tool message should exist"
            assert tool_msg['content'] == PRUNED_TOOL_CONTENT, \
                f"Group {i} tool message should be pruned"

        # Verify: Last 5 groups (group_3 to group_7) should have full content
        for i in range(3, 8):  # group_3 to group_7
            group_id = f"group_{i}"
            tool_msg = next(
                (msg for msg in prepared_messages
                 if msg.get('role') == AgentRole.TOOL
                 and msg.get('tool_call_group_id') == group_id),
                None
            )
            assert tool_msg is not None, f"Group {i} tool message should exist"
            assert tool_msg['content'] == f"Response {i}", \
                f"Group {i} tool message should have full content"


class TestToolCallPruningStructure:
    """Tests for preserving message structure after pruning."""

    def test_tool_message_structure_preserved(self, agent):
        """Test that tool message structure (tool_call_id, group_id, etc.) is preserved after pruning."""
        group_1_id = "group_1"
        agent.tool_call_group_ids.append(group_1_id)

        original_tool_msg = {
            "role": AgentRole.TOOL,
            "tool_call_id": "call_123",
            "tool_call_group_id": group_1_id,
            "content": "Original content",
            "name": "load",
            "arguments": {"file_path": "test.txt"},
            "captured_logs": "logs"
        }
        agent.messages.append({
            "role": AgentRole.ASSISTANT,
            "content": "Call tool",
            "tool_calls": [{"id": "call_123", "type": "function", "function": {"name": "load", "arguments": "{}"}}]
        })
        agent.messages.append(original_tool_msg)

        # Prepare messages (will prune since keep_last_k=1 but this is the only group)
        # Actually, if there's only one group and keep_last_k=1, it should keep it
        # Let's add another group to ensure pruning
        group_2_id = "group_2"
        agent.tool_call_group_ids.append(group_2_id)
        agent.messages.append({
            "role": AgentRole.ASSISTANT,
            "content": "Call another tool",
            "tool_calls": [{"id": "call_456", "type": "function", "function": {"name": "load", "arguments": "{}"}}]
        })
        agent.messages.append({
            "role": AgentRole.TOOL,
            "tool_call_id": "call_456",
            "tool_call_group_id": group_2_id,
            "content": "Response 2"
        })

        prepared_messages = agent._prepare_messages(
            agent.messages,
            last_k_tool_call_group=agent.keep_last_k_tool_call_contexts
        )

        # Find pruned tool message
        pruned_tool_msg = next(
            (msg for msg in prepared_messages
             if msg.get('role') == AgentRole.TOOL
             and msg.get('tool_call_id') == "call_123"),
            None
        )

        assert pruned_tool_msg is not None
        # Verify structure is preserved
        assert pruned_tool_msg['tool_call_id'] == original_tool_msg['tool_call_id']
        assert pruned_tool_msg['tool_call_group_id'] == original_tool_msg['tool_call_group_id']
        assert pruned_tool_msg['name'] == original_tool_msg['name']
        assert pruned_tool_msg['arguments'] == original_tool_msg['arguments']
        # Only content should be changed
        assert pruned_tool_msg['content'] == PRUNED_TOOL_CONTENT
        assert pruned_tool_msg['content'] != original_tool_msg['content']


if __name__ == "__main__":
    from .base import run_tests_with_report

    sys.exit(run_tests_with_report(__file__, 'agent_tool_call_pruning'))

