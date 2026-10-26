package org.asc.foundation
import android.widget.*
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class NativeUiTest {
    @Test fun nativeJoinAndReplacementRequireFreshOwnerTrustBeforeAnyDispatch() {
        ActivityScenario.launch(MainActivity::class.java).use {s ->s.onActivity {a ->
            val root=a.window.decorView
            root.findViewWithTag<Button>("tab-1").performClick()
            for(tag in listOf("native-join","replace-native-code")) {
                root.findViewWithTag<Button>(tag).performClick()
                assertTrue(root.findViewWithTag<TextView>("join-result").text.toString().contains("đối chiếu",ignoreCase=true))
            }
            assertNotNull(root.findViewWithTag<Button>("resume-native-join"))
            assertNotNull(root.findViewWithTag<Button>("native-join-status"))
            assertFalse(root.findViewWithTag<EditText>("join-code").isSaveEnabled)
        }}
    }
    @Test fun actualUiUnknownsTrustGateAndNoSavedOneUseCode() {
        ActivityScenario.launch(MainActivity::class.java).use {s ->
            s.onActivity {a ->
                val root=a.window.decorView
                root.findViewWithTag<Button>("tab-1").performClick()
                assertEquals(android.view.View.VISIBLE,root.findViewWithTag<android.view.View>("page-1").visibility)
                val code=root.findViewWithTag<EditText>("join-code")
                assertFalse(code.isSaveEnabled);assertTrue(code.inputType and android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD !=0)
                root.findViewWithTag<Button>("save-draft").performClick()
                assertTrue(root.findViewWithTag<TextView>("join-result").text.toString().contains("Cần đối chiếu"))
                val cluster=root.findViewWithTag<TextView>("cluster-status").text.toString()
                assertTrue(cluster.contains("Quorum: UNKNOWN"));assertTrue(cluster.contains("Replica protection: UNKNOWN"))
                assertFalse(cluster.contains("ONLINE"))
                code.setText("123456abcdef")
            }
            s.moveToState(androidx.lifecycle.Lifecycle.State.CREATED)
            s.moveToState(androidx.lifecycle.Lifecycle.State.RESUMED)
            s.onActivity {a ->assertEquals("",a.window.decorView.findViewWithTag<EditText>("join-code").text.toString())}
        }
    }
}
