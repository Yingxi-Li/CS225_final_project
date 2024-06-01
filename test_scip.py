from pyscipopt import Model, quicksum

model = Model("Example")

x = model.addVar("x")
y = model.addVar("y", vtype="INTEGER")
model.setObjective(x + y)
model.addCons(2*x - y*y >= 0)
model.optimize()
sol = model.getBestSol()
print("x: {}".format(sol[x]))
print("y: {}".format(sol[y]))

model = Model("Example") 