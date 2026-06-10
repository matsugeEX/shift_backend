from ortools.sat.python import cp_model

model = cp_model.CpModel() #制約を登録する入れ物
solver = cp_model.CpSolver() 

#変数を追加する
x = model.new_bool_var("x")
y = model.new_bool_var("y")

model.Add(x+y==1) #x+y==1 という制約を追加 model.Add(条件式) で制約を追加する

status = solver.Solve(model) #solver.Solve(model) で解を探索する

print("status:", status)

print("x =", solver.Value(x))
print("y =", solver.Value(y))

#-----------------------------------------------------------------------------

model_1 = cp_model.CpModel()
solver_1 = cp_model.CpSolver()

workers = ["田中", "佐藤"]
slots = ["朝", "昼"]

x = {}

#xという辞書にforで回したworkerとslotをキーとしてf"{worker}_{slot}"を登録、これは.NewBoolVarより真偽値
for worker in workers:
    for slot in slots:
        x[worker, slot] = model_1.NewBoolVar(f"{worker}_{slot}") 

#slot = "朝" の時、x["田中", "朝"] + x["佐藤", "朝"] == 1 、 朝シフトには1人だけ入れる、というような割り当て 
for slot in slots:
    model_1.Add(
        sum(x[worker, slot] for worker in workers) == 1
    )

#worker = "田中" の時、x["田中", "朝"] + x["田中", "昼"] <= 1 、 田中さんは最大1回しか働けない、というような割り当て
for worker in workers:
    model_1.Add(
        sum(x[worker, slot] for slot in slots) <= 1
    )

status = solver_1.Solve(model_1)

print("status:", status)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    for slot in slots:
        print(slot)
        for worker in workers:
            if solver_1.Value(x[worker, slot]) == 1:
                print(" ", worker)
else:
    print("解なし")