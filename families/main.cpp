#include <boost/multiprecision/cpp_int.hpp>
#include <iostream>
#include <algorithm>
#include <vector>
#include <base_families.cpp>
#include <cstdlib>
#include <execution>
#include <atomic>
#include <mutex>


using namespace boost::multiprecision;
typedef uint512_t bigint;
typedef std::pair<std::vector<uint32_t>, std::vector<std::pair<uint32_t, uint32_t>>> expanded_string;
typedef std::vector<expanded_string> expanded_family;

std::atomic_int MAX_PERSISTENCE = 0;
bigint MAX_INT = 0;
size_t MAX_LEN = 100;
bool printed_return = false;
std::mutex LOCK;

inline void digit_multiply(bigint& num, uint32_t base) {
    bigint WORK_MULT = num;
    num = 1;
    while (WORK_MULT > 1) {
        num *= WORK_MULT % base;
        WORK_MULT /= base;
    }
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

inline uint32_t get_persistence(const bigint& num, uint32_t base) {
    uint32_t persistence = 1;
    bigint WORK_MULT_RET = num;
    while (WORK_MULT_RET >= base) {
        digit_multiply(WORK_MULT_RET, base);
        persistence += 1;
    }
    return persistence;
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
        std::sort(combo.begin(), combo.end());
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

void generate_combos_expanded(
    const std::vector<std::pair<uint32_t, uint32_t>>& data,
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
        if(idx + data[i].second <= length) {
            for(size_t j = idx; j < idx + data[i].second; ++j) {
                combo[j] = data[i].first;
            }
            generate_combos_expanded(data, length, idx + data[i].second, i, combo, base);
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
}

std::vector<int> idempotence_cache(0, 0);

inline int get_idempotence(uint32_t i, uint32_t base, uint32_t onesmod) {
    int ret = 0;
    uint32_t current = onesmod;
    std::vector<int> last_seen(base, 0);
    do {
        /*
        std::cout << "i: " << i << std::endl;
        std::cout << "base: " << base << std::endl;
        std::cout << "onesmod: " << onesmod << std::endl;
        std::cout << "current: " << current << std::endl;
        std::cout << "last: " << last << std::endl;
        */
        last_seen[current] = ret; 
        current = (current * i) % base;
        ++ret;
    } while(last_seen[current] == 0);
    return ret - last_seen[current];
}

int max_idempotence(uint32_t i, uint32_t base) {
    int max = 0;
    for(uint32_t j = 1; j < base; ++j) {
        int idem = get_idempotence(i, base, j);
        idempotence_cache[i * base + j] = idem;
        max = std::max(max, idem);
    }
    return max;
}

void process_string_combo(
    expanded_family& ret,
    expanded_string& combo, 
    const pstring& original_string, 
    const std::vector<int>& used,
    uint32_t base, 
    uint32_t max_power
) {
    uint32_t onesmod = 1;
    uint32_t basepow = std::pow(base, max_power);
    for(auto& i : combo.first) {
        onesmod = onesmod * i % basepow;
        //std::cout << i << " ";
    }
    for(size_t i = 0; i < original_string.second.size(); ++i) {
        int idempotence = idempotence_cache[original_string.second[i] * basepow + onesmod];
        if(idempotence > 0) {
            combo.second.emplace_back(original_string.second[i], idempotence);
        }
        if(used[i] > idempotence) {
            combo.second.resize(0);
            return;
        }
        //std::cout << "(" << original_string.second[i] << "*" << idempotence << ")*";
    }
    for(uint32_t power = 2; power <= max_power; ++power) {
        if(onesmod % uint32_t(std::pow(base, power)) < std::pow(base, power - 1)) {
            combo.second.resize(0);
            return;
        }
    }
    const std::lock_guard<std::mutex> l(LOCK);
    ret.push_back(combo);
    //std::cout << std::endl;
    combo.second.resize(0);
}

void generate_string_combos(
    expanded_family& ret,
    expanded_string& current_combo,
    const pstring& original_string,
    std::vector<int>& maxes,
    std::vector<int>& used,
    uint32_t base,
    uint32_t max_power,
    size_t max_len,
    size_t last_star_idx,
    size_t idx
) {
    if(idx >= max_len) {
        process_string_combo(ret, current_combo, original_string, used, base, max_power);
    } else {
        for(size_t i = last_star_idx; i < original_string.second.size(); ++i) {
            // try all valid stars, updating maxes to track what's been used
            if(maxes[i] > 0) { 
                --maxes[i];
                ++used[i];
                current_combo.first[idx] = original_string.second[i];
                generate_string_combos(ret, current_combo, original_string, maxes, used, base, max_power, max_len, i, idx + 1);
                ++maxes[i];
                --used[i];
            }
        }
    }
}

void expand_string(expanded_family& fam, const pstring& s, uint32_t base, uint32_t max_power) {
    int onesmod =  1;
    uint32_t basepow = std::pow(base, max_power);
    for(auto& o : s.first) {
        onesmod *= o;
    }
    
    // Construct list of max idempotences for each star
    std::vector<int> maxes;
    idempotence_cache.resize((1 + *std::max_element(s.second.begin(), s.second.end())) * basepow);
    for(auto& i : s.second) {
        maxes.push_back(max_idempotence(i, basepow) - 1);
        std::cout << "Star: " << i << " " << maxes[maxes.size()-1] + 1 << std::endl;;
    }
    int sum = std::accumulate(maxes.begin(), maxes.end(), 0);
    std::vector<int> used(maxes.size(), 0);

    // loop through and create valid strings
    for(size_t i = 0; i <= sum; ++i) {
        std::cout << i << "/" << sum << "\r";
        expanded_string current_combo;
        current_combo.first = s.first;
        current_combo.first.resize(current_combo.first.size() + i);
        generate_string_combos(fam, current_combo, s, maxes, used, base, max_power, current_combo.first.size(), 0, s.first.size());
    }
    std::cout << std::endl;
}

expanded_family expand_base_family(const family& fam, uint32_t base, uint32_t max_power) {
    expanded_family ret;
    auto expand = [&](const pstring& s) {
        expand_string(ret, s, base, max_power);
    };
    std::for_each(std::execution::par, fam.cbegin(), fam.cend(), expand);
    std::cout << "Total strings: " << fam.size() << std::endl;
    return std::move(ret);
}


void print_combos(uint32_t base) {
    const auto& families = BASE_FAMILIES[base];

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
        std::for_each(std::execution::par, families.cbegin(), families.cend(), generate);
    }
}

void print_combos_expanded(uint32_t base, const expanded_family& fam) {
    for(size_t i = 1; i < MAX_LEN; i++) {
        std::cout << "Generating combinations of length " << i << "\r";
        printed_return = true;
        auto generate = [&](const expanded_string& pair) {
            auto& ones = pair.first;
            auto& stars = pair.second;
            // generate combinations of length i
            std::vector<uint32_t> current_combo(i, 0);
            if(ones.size() > i) {
                return;
            }
            size_t k=0;
            for (; k < ones.size(); ++k) {
                current_combo[k] = ones[k];
            }
            generate_combos_expanded(stars, i, k, 0, current_combo, base);
        };
        std::for_each(std::execution::par, fam.cbegin(), fam.cend(), generate);
    }
}

int main(int argc, char** argv) {
    uint32_t max_power = atoi(argv[argc - 2]);
    uint32_t base = atoi(argv[argc - 3]);
    MAX_LEN = atoi(argv[argc - 1]);
    std::cout.setf( std::ios_base::unitbuf );
    std::cout << base << std::endl;
    if(max_power == 1) {
        print_combos(base);
    } else {
        const auto& families = expand_base_family(BASE_FAMILIES[base], base, max_power);
        print_combos_expanded(base, families);
    }
    return 0;
}
