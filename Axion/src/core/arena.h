#pragma once
#include <cstddef>
#include <vector>
#include <memory>

namespace axion {

class Arena {
    static constexpr size_t BLOCK_SIZE = 64 * 1024;
    std::vector<std::unique_ptr<char[]>> blocks_;
    size_t offset_ = BLOCK_SIZE; // force alloc on first use

public:
    void* alloc(size_t size, size_t align = alignof(std::max_align_t));
    void reset();

    template<typename T, typename... Args>
    T* create(Args&&... args) {
        void* mem = alloc(sizeof(T), alignof(T));
        return new (mem) T(std::forward<Args>(args)...);
    }
};

} // namespace axion
