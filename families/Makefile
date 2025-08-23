build:
	g++ -pthread -std=c++20 -fopenmp -fprofile-generate -Ofast -march=native -mtune=native -I . -g main.cpp -o base_family_checker -ltbb
	./base_family_checker 10 3 50
	g++ -pthread -std=c++20 -fopenmp -fprofile-use -Ofast -march=native -mtune=native -I . -g main.cpp -o base_family_checker -ltbb

debug:
	g++ -O0 -I . -g main.cpp -o base_family_checker -ltbb
	gdb ./base_family_checker

profile:
	valgrind --tool=callgrind --dump-instr=yes --simulate-cache=yes --collect-jumps=yes ./base_family_checker 11 2 55

full:
	g++ -DFULL_BASES -pthread -std=c++20 -fopenmp -fprofile-generate -Ofast -march=native -mtune=native -I . -g main.cpp -o base_family_checker -ltbb
	./base_family_checker 10 3 50
	g++ -DFULL_BASES -pthread -std=c++20 -fopenmp -fprofile-use -Ofast -march=native -mtune=native -I . -g main.cpp -o base_family_checkera-ltbb

