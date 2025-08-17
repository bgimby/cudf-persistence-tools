#include <boost/multiprecision/cpp_int.hpp>
#include <iostream>
#include <algorithm>
#include <vector>
#include <base_families.cpp>
#include <cstdlib>
#include <execution>


using namespace boost::multiprecision;
typedef uint512_t bigint;

uint32_t MAX_PERSISTENCE = 0;
bigint MAX_INT = 0;
size_t MAX_LEN = 100;
bigint WORK_MULT = 0;
bool printed_return = false;

inline void digit_multiply(bigint& num, uint32_t base) {
    // Can we avoid this copy?
    WORK_MULT -= 1;
    WORK_MULT += num;
    num *= 0;
    num += 1;
    while (WORK_MULT > 1) {
        num *= WORK_MULT % base;
        WORK_MULT /= base;
    }
}

inline uint32_t get_persistence(bigint& num, uint32_t base) {
    uint32_t persistence = 1;
    while (num >= base) {
        digit_multiply(num, base);
        persistence += 1;
    }
    return persistence;
}

bigint value_in_base(const std::vector<uint32_t>& num, uint32_t base) {
    bigint ret = 0;
    bigint base_val = 1;
    for (auto d = num.rbegin(); d != num.rend(); ++d) {
        ret += (*d) * base_val;
        base_val *= base;
    }
    return ret;
}

void process_combo(std::vector<uint32_t>& combo, uint32_t base) {
    bigint u = 1;
    //std::cout << "Combo: ";
    for (auto& val : combo) {
        //std::cout << val << "";
        u *= val;
    }
    uint32_t persistence = get_persistence(u, base);
    //std::cout << std::endl;
    //std::cout << "Num: " << u << std::endl;
    //std::cout << "Persistence: " << persistence << std::endl;

    if (persistence >= MAX_PERSISTENCE) {
        // recalculate u since it's been clobbered by get_persistence to avoid unnecessary copy
        u = 1;
        for (auto& val : combo) {
            //std::cout << val << "";
            u *= val;
        }
        bigint num_in_base = value_in_base(combo, base);
        if (persistence > MAX_PERSISTENCE || num_in_base < MAX_INT) {
            if (printed_return) {
                std::cout << std::endl;
                printed_return = false;
            }
            std::cout << "New max: ";
            for (auto& val : combo) {
                std::cout << val << " ";
            }
            std::cout << std::endl;
            std::cout << "In base 10: " << num_in_base << std::endl;
            std::cout << "Persistence: " << persistence << std::endl;
            MAX_PERSISTENCE = persistence;
            MAX_INT = num_in_base;
        }
    }
}

void generate_combos(
    const std::vector<uint32_t>& data,
    uint32_t length,
    uint32_t idx,
    size_t last_idx,
    std::vector<uint32_t>& combo,
    uint32_t base) {
    if (idx >= length) {
        process_combo(combo, base);
        return;
    }
    for (size_t i=last_idx; i<data.size(); i++){
        combo[idx] = data[i];
        generate_combos(data, length, idx + 1, i, combo, base);
    }
//    for (auto& i : data) {
//        if (i < last_val) {
//            continue;
//        }
//        combo[idx] = i;
//        //std::cout << start_idx << i << length << "l" << std::endl;
//        generate_combos(data, length, idx + 1, i, combo);
//    }
}

void print_combos(uint32_t base) {
    auto families = BASE_FAMILIES[base];

    for (size_t i = 1; i < MAX_LEN; i++) {
        std::cout << "Generating combinations of length " << i << "\r";
        printed_return = true;
        auto generate = [&](const std::pair<std::vector<uint32_t>, std::vector<uint32_t>>& pair) {
            auto& ones = pair.first;
            auto& vec = pair.second;
            // generate combinations of length i
            std::vector<uint32_t> current_combo(i, 0);
            size_t k=0;
            for (; k < std::min(i, ones.size()); ++k) {
                current_combo[k] = ones[k];
            }
            generate_combos(vec, i, k, 0, current_combo, base);
        };
        std::for_each(std::execution::par_unseq, families.cbegin(), families.cend(), generate);
    }
}

int main(int argc, char** argv) {
    uint32_t base = atoi(argv[argc - 2]);
    MAX_LEN = atoi(argv[argc - 1]);
    std::cout.setf( std::ios_base::unitbuf );
    std::cout << base << std::endl;
    print_combos(base);
    return 0;
}
