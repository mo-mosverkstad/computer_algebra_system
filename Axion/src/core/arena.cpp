#include "core/arena.h"

namespace axion {

void* Arena::alloc(size_t size, size_t align) {
    // Align offset
    offset_ = (offset_ + align - 1) & ~(align - 1);
    if (offset_ + size > BLOCK_SIZE) {
        size_t block_size = (size > BLOCK_SIZE) ? size : BLOCK_SIZE;
        blocks_.push_back(std::make_unique<char[]>(block_size));
        offset_ = 0;
    }
    void* ptr = blocks_.back().get() + offset_;
    offset_ += size;
    return ptr;
}

void Arena::reset() {
    blocks_.clear();
    offset_ = BLOCK_SIZE;
}

} // namespace axion
