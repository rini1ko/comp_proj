import json
import visual

class Record:
    def __init__(self, key, value):
        self.key = int(key)
        self.value = value

    def __lt__(self, other):
        return self.key < other.key

    def __gt__(self, other):
        return self.key > other.key

    def __eq__(self, other):
        return self.key == other.key

    def __ge__(self, other):
        return self.key >= other.key

    def __le__(self, other):
        return self.key <= other.key

    def __repr__(self):
        return f"({self.key}: {self.value})"


class DatabaseEngine:
    def __init__(self, tree_engine):
        self.tree = tree_engine

    def execute(self, query):
        query = query.strip()
        parts = query.split(maxsplit=2)

        if not parts:
            return "Error: Empty query"
        command=parts[0].upper()
        if command == "INSERT":
            if len(parts) < 3:
                return "Error: Invalid format. Expected: INSERT <id> <data>"
            try:
                record_id=int(parts[1])
                try:
                    data=json.loads(parts[2])
                except json.JSONDecodeError:
                    data= parts[2]

                new_record=Record(record_id, data)
                found, _ =self.tree.find(new_record)

                if found:
                    return f"Error: Record {record_id} already exists. Use UPDATE."
                else:
                    visual.set_label(f"INSERT: {record_id}")
                    self.tree.add(new_record)
                    visual.save_tree_snapshot(self.tree)
                    return "OK: Record added"
            except ValueError:
                return "Error: ID must be a number"

        elif command == "UPDATE":
            if len(parts) < 3:
                return "Error: Invalid format. Expected: UPDATE <id> <data>"
            try:
                record_id= int(parts[1])
                try:
                    data= json.loads(parts[2])
                except json.JSONDecodeError:
                    data= parts[2]
                dummy=Record(record_id, None)
                found, result =self.tree.find(dummy)

                if found:
                    visual.set_label(f"UPDATE: {record_id}")
                    # Універсальне діставання запису для всіх типів дерев
                    record = result.data if hasattr(result, 'data') else result
                    record.value = data
                    visual.save_tree_snapshot(self.tree)
                    return f"OK: Record {record_id} updated"
                else:
                    return f"Error: Record {record_id} not found"
            except ValueError:
                return "Error: ID must be a number"

        elif command == "SELECT":
            if len(parts) < 2:
                return "Error: Invalid format. Expected: SELECT <id>"
            try:
                record_id = int(parts[1])
                dummy = Record(record_id, None)
                found, result = self.tree.find(dummy)
                if found:
                    record = result.data if hasattr(result, 'data') else result
                    return f"OK: Found {record.value}"
                else:
                    return "Error: Record not found"
            except ValueError:
                return "Error: ID must be a number"

        elif command == "DELETE":
            if len(parts) < 2:
                return "Error: Invalid format. Expected: DELETE <id>"
            try:
                record_id=int(parts[1])
                dummy=Record(record_id, None)
                found, _ = self.tree.find(dummy)
                if found:
                    visual.set_label(f"DELETE: {record_id}")
                    self.tree.delete(dummy)
                    visual.save_tree_snapshot(self.tree)
                    return f"OK: Record {record_id} deleted"
                else:
                    return "Error: Record not found"
            except ValueError:
                return "Error: ID must be a number"

        else:
            return f"Error: Unknown command '{command}'"