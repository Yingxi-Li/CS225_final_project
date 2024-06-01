import random

# Number of cities
n = 50

# Generate random distances (for demonstration purposes)
distances = [[random.randint(1, 100) for _ in range(n)] for _ in range(n)]
print(distances[1][2])

with open("tsp.lp", "w") as file:
    file.write("Minimize\n obj: ")
    file.write(" + ".join(f"{str(distances[i][j])} x{i+1}{j+1}" for i in range(n) for j in range(n) if i != j))
    file.write("\nSubject To\n")
    
    # Each city must be entered exactly once
    for i in range(1, n+1):
        file.write(f" c{i}: " + " + ".join(f"x{i}{j}" for j in range(1, n+1) if i != j) + " = 1\n")
    
    # Each city must be left exactly once
    for j in range(1, n+1):
        file.write(f" c{n+j}: " + " + ".join(f"x{i}{j}" for i in range(1, n+1) if i != j) + " = 1\n")
    
    # MTZ constraints
    constraint_count = 2 * n
    for i in range(2, n+1):
        for j in range(2, n+1):
            if i != j:
                file.write(f" u{i}u{j}: u{i} - u{j} + {n} x{i}{j} <= {n-1}\n")
                constraint_count += 1

    file.write("Bounds\n")
    for i in range(1, n+1):
        for j in range(1, n+1):
            if i != j:
                file.write(f" 0 <= x{i}{j} <= 1\n")
    
    file.write("Binaries\n")
    for i in range(1, n+1):
        for j in range(1, n+1):
            if i != j:
                file.write(f" x{i}{j}\n")
                
    file.write("General\n")
    for i in range(2, n+1):
        file.write(f" u{i}\n")
    
    file.write("End\n")
