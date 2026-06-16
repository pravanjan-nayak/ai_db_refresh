from db.dba_tasks import match_known_task

print(match_known_task("show database status"))
print(match_known_task("show invalid objects in hr"))
print(match_known_task("show all tables in scott"))
print(match_known_task("take logical backup"))