/**
 * Smoke test to verify native test environment works.
 * This minimal test validates the PlatformIO test infrastructure.
 */

#include <unity.h>

void setUp(void) {
    // Called before each test
}

void tearDown(void) {
    // Called after each test
}

void test_smoke_passes(void) {
    TEST_ASSERT_TRUE(true);
}

void test_environment_defined(void) {
    // Verify build flags are working
    #ifdef ENVIRONMENT
        TEST_ASSERT_TRUE(true);
    #else
        TEST_FAIL_MESSAGE("ENVIRONMENT not defined");
    #endif
}

int main(int argc, char **argv) {
    UNITY_BEGIN();
    RUN_TEST(test_smoke_passes);
    RUN_TEST(test_environment_defined);
    return UNITY_END();
}
