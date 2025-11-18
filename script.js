document.addEventListener("DOMContentLoaded", () => {
  const askBtn = document.getElementById("askBtn");
  const videoIdInput = document.getElementById("videoId");
  const questionInput = document.getElementById("question");
  const answerDiv = document.getElementById("answer");

  askBtn.addEventListener("click", async () => {
    const videoId = videoIdInput.value.trim();
    const question = questionInput.value.trim();

    // Input validation
    if (!videoId || !question) {
      answerDiv.textContent = "⚠️ Please enter both the YouTube video URL or ID and your question.";
      return;
    }

    // Disable button & show loading text
    askBtn.disabled = true;
    askBtn.textContent = "⏳ Processing...";
    answerDiv.textContent = "🧠 Fetching transcript and analyzing your question...";

    try {
      // Full Hugging Face backend endpoint
      const response = await fetch("https://Gyanendra87-VidQuery.hf.space/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_url: videoId,   // supports full URL or ID
          question: question
        })
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("⚠️ Transcript not available for this video.");
        } else if (response.status === 500) {
          throw new Error("🚨 Server error! Please try again later.");
        } else {
          throw new Error(`Unexpected error (${response.status}).`);
        }
      }

      const data = await response.json();
      console.log("✅ Backend Response:", data);

      // Display answer or fallback
      if (data.answer) {
        answerDiv.textContent = `💬 ${data.answer.trim()}`;
      } else {
        answerDiv.textContent = "🤔 No clear answer found in the transcript.";
      }

    } catch (error) {
      console.error("❌ Error fetching answer:", error);
      if (error.message.includes("Failed to fetch")) {
        answerDiv.textContent = "🌐 Cannot connect to backend. Check if the Hugging Face Space is live.";
      } else {
        answerDiv.textContent = error.message;
      }
    } finally {
      // Re-enable button
      askBtn.disabled = false;
      askBtn.textContent = "Ask";
    }
  });
});
