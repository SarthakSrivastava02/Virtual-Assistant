import ast
import operator
import math
import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
import database

# Safe operator mapping for mathematical AST evaluator
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

SAFE_FUNCTIONS = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "abs": abs,
    "round": round,
    "factorial": math.factorial,
    "pi": math.pi,
    "e": math.e,
}

class SafeCalculator:
    """
    Evaluates mathematical expressions strictly using AST parsing,
    completely preventing arbitrary code execution.
    """
    @classmethod
    def evaluate(cls, expression_str: str) -> Tuple[bool, Any, str]:
        # Normalize expression (replace words/symbols)
        expr = expression_str.strip()
        expr = expr.replace("^", "**").replace("×", "*").replace("÷", "/")
        expr = re.sub(r'(?i)calculate\s*', '', expr)
        expr = re.sub(r'(?i)what is\s*', '', expr)
        expr = re.sub(r'\?*$', '', expr).strip()

        try:
            node = ast.parse(expr, mode='eval')
            result = cls._eval_node(node.body)
            # Format nicely
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return True, result, f"Result: {result}"
        except Exception as e:
            return False, None, f"Could not calculate expression '{expr}': {str(e)}"

    @classmethod
    def _eval_node(cls, node):
        if isinstance(node, ast.Constant): # number or string literal
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numbers are permitted")
        elif isinstance(node, ast.BinOp): # binary op: a + b
            op_type = type(node.op)
            if op_type not in SAFE_OPERATORS:
                raise ValueError(f"Operator {op_type.__name__} is not supported")
            left = cls._eval_node(node.left)
            right = cls._eval_node(node.right)
            if op_type == ast.Div and right == 0:
                raise ZeroDivisionError("Division by zero")
            return SAFE_OPERATORS[op_type](left, right)
        elif isinstance(node, ast.UnaryOp): # unary op: -x
            op_type = type(node.op)
            if op_type not in SAFE_OPERATORS:
                raise ValueError(f"Operator {op_type.__name__} is not supported")
            operand = cls._eval_node(node.operand)
            return SAFE_OPERATORS[op_type](operand)
        elif isinstance(node, ast.Name): # e.g. pi, e
            if node.id.lower() in SAFE_FUNCTIONS:
                val = SAFE_FUNCTIONS[node.id.lower()]
                if not callable(val):
                    return val
            raise ValueError(f"Unknown variable or constant: {node.id}")
        elif isinstance(node, ast.Call): # e.g. sqrt(16)
            if isinstance(node.func, ast.Name):
                func_name = node.func.id.lower()
                if func_name in SAFE_FUNCTIONS and callable(SAFE_FUNCTIONS[func_name]):
                    args = [cls._eval_node(arg) for arg in node.args]
                    return SAFE_FUNCTIONS[func_name](*args)
            raise ValueError("Unsupported function call")
        else:
            raise ValueError(f"Unsupported syntax: {type(node).__name__}")


class DateTimeTool:
    """Provides current time, date, day of the week, and calendar information."""
    @staticmethod
    def get_info() -> Dict[str, Any]:
        now = datetime.now()
        return {
            "current_time_12h": now.strftime("%I:%M:%S %p"),
            "current_time_24h": now.strftime("%H:%M:%S"),
            "date": now.strftime("%B %d, %Y"),
            "day_of_week": now.strftime("%A"),
            "iso_timestamp": now.isoformat(),
            "year": now.year,
            "month": now.strftime("%B"),
            "day": now.day
        }

    @classmethod
    def format_reply(cls) -> str:
        info = cls.get_info()
        return (
            f"📅 **Date:** {info['day_of_week']}, {info['date']}\n"
            f"⏰ **Current Time:** {info['current_time_12h']} ({info['current_time_24h']})"
        )


class TextTools:
    """Extractive summarization, sentence highlighting, and tone rewriting."""
    @staticmethod
    def extractive_summary(text: str, num_sentences: int = 3) -> Dict[str, Any]:
        if not text or len(text.strip()) < 50:
            return {"summary": text, "key_points": [text]}

        # Split into sentences
        raw_sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 15]
        
        if len(sentences) <= num_sentences:
            return {"summary": " ".join(sentences), "key_points": sentences}

        # Calculate word frequency weights
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        stopwords = {
            "the", "and", "that", "this", "with", "from", "for", "have", "are", "was",
            "were", "which", "will", "would", "there", "their", "they", "about"
        }
        word_freq = {}
        for w in words:
            if w not in stopwords:
                word_freq[w] = word_freq.get(w, 0) + 1

        # Score sentences
        sentence_scores = []
        for idx, s in enumerate(sentences):
            s_words = re.findall(r'\b[a-zA-Z]{3,}\b', s.lower())
            score = sum(word_freq.get(w, 0) for w in s_words) / (len(s_words) + 1)
            # Boost first and last sentences
            if idx == 0 or idx == len(sentences) - 1:
                score *= 1.3
            sentence_scores.append((score, idx, s))

        # Select top sentences preserving original sequence
        sentence_scores.sort(key=lambda x: x[0], reverse=True)
        top_selected = sorted(sentence_scores[:num_sentences], key=lambda x: x[1])

        key_points = [item[2] for item in top_selected]
        summary_text = " ".join(key_points)
        return {
            "summary": summary_text,
            "key_points": key_points
        }

    @staticmethod
    def rewrite_text(text: str, style: str = "academic") -> str:
        style = style.lower()
        if style == "academic":
            prefix = "Formal Academic Tone:\n"
            return prefix + text
        elif style == "concise":
            sentences = re.split(r'(?<=[.!?])\s+', text.strip())
            return "Concise Summary:\n• " + "\n• ".join(sentences[:3])
        elif style == "bullet_points":
            sentences = re.split(r'(?<=[.!?])\s+', text.strip())
            return "Key Points:\n" + "\n".join([f"• {s}" for s in sentences if s])
        return text


class IntentDetector:
    """
    Classifies user intent from natural language input using keyword
    patterns, regex, and linguistic heuristics.
    """
    CALC_PATTERNS = [
        r'^\s*[\d\.\(\)\+\-\*\/\^% ]+\s*$',
        r'(?i)^\s*(calculate|compute|solve|evaluate)\s+[\d\.\(\)\+\-\*\/\^%\s\w]+$',
        r'^\s*\d+\s*[\+\-\*\/]\s*\d+',
        r'(?i)\bsqrt\(\s*\d+(\.\d+)?\s*\)',
        r'(?i)^\s*what\s+is\s+[\d\.\(\)\+\-\*\/\^\s]+\?*\s*$'
    ]

    DATETIME_PATTERNS = [
        r'(?i)\b(what time is it|current time|what is the time|tell me the time)\b',
        r'(?i)\b(what is today\'?s date|what date is it|what\'?s the date|current date|today\'?s date)\b',
        r'(?i)\b(what day is it|which day is today)\b'
    ]

    TODO_PATTERNS = [
        r'(?i)\b(add|create|new)\s+(task|todo|to-do)\b',
        r'(?i)\b(add|create)\s+.+?\s+to\s+(my\s+)?(todos|to-dos|tasks|to-do list)\b',
        r'(?i)\b(show|list|get|view)\s+(my\s+)?(todos|to-dos|tasks|to-do list)\b',
        r'(?i)\b(complete|finish|done|check off)\s+(task|todo|to-do|#\d+|\d+)\b',
        r'(?i)\b(delete|remove)\s+(task|todo|to-do|#\d+|\d+)\b',
        r'(?i)\b(todos|to-dos|to-do list)\b'
    ]

    SUMMARIZE_PATTERNS = [
        r'(?i)^(summarize|summarise|give a summary of|briefly explain)\b',
        r'(?i)\b(tldr|key takeaways|bullet points of)\b'
    ]

    @classmethod
    def detect_intent(cls, message: str) -> str:
        msg = message.strip()

        # Check Datetime
        for pattern in cls.DATETIME_PATTERNS:
            if re.search(pattern, msg):
                return "datetime"

        # Check Todo
        for pattern in cls.TODO_PATTERNS:
            if re.search(pattern, msg):
                return "todo"

        # Check Calculator
        for pattern in cls.CALC_PATTERNS:
            if re.search(pattern, msg):
                return "calculation"

        # Check Summarize
        for pattern in cls.SUMMARIZE_PATTERNS:
            if re.search(pattern, msg):
                return "summarize"

        return "general"


class TaskExecutor:
    """Orchestrates tools and task executions."""

    @staticmethod
    def execute(intent: str, message: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        parameters = parameters or {}

        if intent == "calculation":
            success, result, explanation = SafeCalculator.evaluate(message)
            return {
                "success": success,
                "task_type": "calculation",
                "result": result,
                "message": explanation
            }

        elif intent == "datetime":
            return {
                "success": True,
                "task_type": "datetime",
                "result": DateTimeTool.get_info(),
                "message": DateTimeTool.format_reply()
            }

        elif intent == "todo":
            msg = message.strip()
            # Detect sub-action
            # 1. Add todo: e.g. "add buy milk to my todos"
            add_match = re.search(r'(?i)(?:add|create)\s+(?:task|todo|to-do)?\s*[:"\']?([^"\']+)["\']?\s*(?:to\s+(?:my\s+)?(?:todos|tasks|to-do list))?', msg)
            if "add" in msg.lower() or "create" in msg.lower():
                clean_task = re.sub(r'(?i)^(add|create)\s+(task|todo|to-do)?\s*', '', msg)
                clean_task = re.sub(r'(?i)\s+to\s+(my\s+)?(todos|tasks|to-do list)$', '', clean_task).strip()
                if clean_task:
                    todo_id = database.add_todo(clean_task)
                    todos = database.get_todos()
                    return {
                        "success": True,
                        "task_type": "todo",
                        "action": "added",
                        "result": todos,
                        "message": f"✅ Added to-do #{todo_id}: **{clean_task}**"
                    }

            # 2. List todos
            if any(k in msg.lower() for k in ["show", "list", "view"]):
                todos = database.get_todos()
                if not todos:
                    msg_out = "📝 Your to-do list is currently empty!"
                else:
                    lines = ["📝 **Your Current To-Do List:**"]
                    for t in todos:
                        status = "✓" if t["completed"] else "○"
                        lines.append(f"{status} **#{t['id']}**: {t['task']}")
                    msg_out = "\n".join(lines)
                return {
                    "success": True,
                    "task_type": "todo",
                    "action": "list",
                    "result": todos,
                    "message": msg_out
                }

            # 3. Complete todo
            comp_match = re.search(r'(?i)(?:complete|finish|done|check off)\s+(?:task|todo|#)?\s*(\d+)', msg)
            if comp_match:
                t_id = int(comp_match.group(1))
                updated = database.update_todo(t_id, completed=True)
                todos = database.get_todos()
                return {
                    "success": updated,
                    "task_type": "todo",
                    "action": "completed",
                    "result": todos,
                    "message": f"✅ Marked task #{t_id} as completed!" if updated else f"Task #{t_id} not found."
                }

            # 4. Delete todo
            del_match = re.search(r'(?i)(?:delete|remove)\s+(?:task|todo|#)?\s*(\d+)', msg)
            if del_match:
                t_id = int(del_match.group(1))
                deleted = database.delete_todo(t_id)
                todos = database.get_todos()
                return {
                    "success": deleted,
                    "task_type": "todo",
                    "action": "deleted",
                    "result": todos,
                    "message": f"🗑️ Deleted task #{t_id}." if deleted else f"Task #{t_id} not found."
                }

            # Default list
            todos = database.get_todos()
            return {
                "success": True,
                "task_type": "todo",
                "action": "list",
                "result": todos,
                "message": f"You currently have {len(todos)} task(s) on your list."
            }

        elif intent == "summarize":
            input_text = parameters.get("text", message)
            res = TextTools.extractive_summary(input_text)
            return {
                "success": True,
                "task_type": "summarize",
                "result": res,
                "message": res["summary"]
            }

        return {
            "success": False,
            "task_type": "unknown",
            "result": None,
            "message": "Unrecognized task type."
        }

# Global singleton
task_executor = TaskExecutor()
