build:
	g++ -fprofile-generate -Ofast -march=native -mtune=native -I . -g main.cpp -o base_family_checker
	./base_family_checker 10 3
	g++ -fprofile-use -Ofast -march=native -mtune=native -I . -g main.cpp -o base_family_checker

debug:
	g++ -O0 -I . -g main.cpp -o base_family_checker
	gdb ./base_family_checker

profile:
	valgrind --tool=callgrind --dump-instr=yes --simulate-cache=yes --collect-jumps=yes ./base_family_checker 10 3
