import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TrackScrollCard } from "../../components/TikTokScroll/TrackScrollCard";

const MOCK_TRACK = {
  row_index: 1,
  name: "Bohemian Rhapsody",
  artist: "Queen",
  preview_url: null,
  artwork_url: "https://example.com/art.jpg",
  youtube_id: null,
  tags: ["classic rock", "70s"],
};

describe("TrackScrollCard", () => {
  describe("summary card variant", () => {
    it("renders children when isSummaryCard is true", () => {
      render(
        <TrackScrollCard isSummaryCard data-index={0}>
          <p>Summary content</p>
        </TrackScrollCard>
      );
      expect(screen.getByText("Summary content")).toBeInTheDocument();
    });

    it("does not render track info in summary mode", () => {
      render(
        <TrackScrollCard isSummaryCard track={MOCK_TRACK} data-index={0}>
          <p>Summary</p>
        </TrackScrollCard>
      );
      expect(screen.queryByText("Bohemian Rhapsody")).not.toBeInTheDocument();
    });
  });

  describe("track card variant", () => {
    it("renders the track name", () => {
      render(
        <TrackScrollCard track={MOCK_TRACK} isActive={false} data-index={0} />
      );
      expect(screen.getByText("Bohemian Rhapsody")).toBeInTheDocument();
    });

    it("renders the artist name", () => {
      render(
        <TrackScrollCard track={MOCK_TRACK} isActive={false} data-index={0} />
      );
      expect(screen.getByText("Queen")).toBeInTheDocument();
    });

    it("renders artwork image when artwork_url is present", () => {
      render(
        <TrackScrollCard track={MOCK_TRACK} isActive={false} data-index={0} />
      );
      const img = screen.getByAltText("Bohemian Rhapsody");
      expect(img).toBeInTheDocument();
      expect(img).toHaveAttribute("src", "https://example.com/art.jpg");
    });

    it("renders placeholder when no artwork_url", () => {
      const noArt = { ...MOCK_TRACK, artwork_url: null };
      render(
        <TrackScrollCard track={noArt} isActive={false} data-index={0} />
      );
      expect(screen.getByText("♪")).toBeInTheDocument();
    });

    it("renders context line when provided", () => {
      render(
        <TrackScrollCard
          track={MOCK_TRACK}
          isActive={false}
          contextLine="Fits the vibe perfectly."
          data-index={0}
        />
      );
      expect(screen.getByText("Fits the vibe perfectly.")).toBeInTheDocument();
    });

    it("does not render context line when not provided", () => {
      render(
        <TrackScrollCard track={MOCK_TRACK} isActive={false} data-index={0} />
      );
      // contextLine is empty/falsy — should not render the element
      expect(screen.queryByRole("paragraph", { name: /context/i })).not.toBeInTheDocument();
    });

    it("renders heart button", () => {
      render(
        <TrackScrollCard track={MOCK_TRACK} isActive={false} data-index={0} />
      );
      expect(screen.getByLabelText("Heart")).toBeInTheDocument();
    });

    it("renders skip button", () => {
      render(
        <TrackScrollCard track={MOCK_TRACK} isActive={false} data-index={0} />
      );
      expect(screen.getByLabelText("Skip")).toBeInTheDocument();
    });

    it("calls onHeart when heart button is clicked", () => {
      const onHeart = vi.fn();
      render(
        <TrackScrollCard
          track={MOCK_TRACK}
          isActive={false}
          onHeart={onHeart}
          data-index={0}
        />
      );
      fireEvent.click(screen.getByLabelText("Heart"));
      expect(onHeart).toHaveBeenCalledOnce();
    });

    it("calls onSkip when skip button is clicked", () => {
      const onSkip = vi.fn();
      render(
        <TrackScrollCard
          track={MOCK_TRACK}
          isActive={false}
          onSkip={onSkip}
          data-index={0}
        />
      );
      fireEvent.click(screen.getByLabelText("Skip"));
      expect(onSkip).toHaveBeenCalledOnce();
    });
  });

  describe("hearted state", () => {
    it("shows filled heart when isHearted is true", () => {
      render(
        <TrackScrollCard
          track={MOCK_TRACK}
          isActive={false}
          isHearted={true}
          data-index={0}
        />
      );
      expect(screen.getByText(/hearted/i)).toBeInTheDocument();
      expect(screen.getByLabelText("Unheart")).toBeInTheDocument();
    });

    it("shows empty heart when isHearted is false", () => {
      render(
        <TrackScrollCard
          track={MOCK_TRACK}
          isActive={false}
          isHearted={false}
          data-index={0}
        />
      );
      expect(screen.getByLabelText("Heart")).toBeInTheDocument();
    });

    it("applies hearted CSS class when isHearted", () => {
      render(
        <TrackScrollCard
          track={MOCK_TRACK}
          isActive={false}
          isHearted={true}
          data-index={0}
        />
      );
      const btn = screen.getByLabelText("Unheart");
      expect(btn.className).toContain("scroll-card__btn--hearted");
    });

    it("does not apply hearted CSS class when not hearted", () => {
      render(
        <TrackScrollCard
          track={MOCK_TRACK}
          isActive={false}
          isHearted={false}
          data-index={0}
        />
      );
      const btn = screen.getByLabelText("Heart");
      expect(btn.className).not.toContain("scroll-card__btn--hearted");
    });
  });

  describe("YouTube fallback", () => {
    it("shows YouTube badge when youtube_id is present and no preview_url", () => {
      const ytTrack = { ...MOCK_TRACK, preview_url: null, youtube_id: "dQw4w9WgXcQ" };
      render(
        <TrackScrollCard track={ytTrack} isActive={false} data-index={0} />
      );
      expect(screen.getByText(/watch on youtube/i)).toBeInTheDocument();
    });

    it("YouTube link points to correct URL", () => {
      const ytTrack = { ...MOCK_TRACK, preview_url: null, youtube_id: "dQw4w9WgXcQ" };
      render(
        <TrackScrollCard track={ytTrack} isActive={false} data-index={0} />
      );
      const link = screen.getByText(/watch on youtube/i).closest("a");
      expect(link).toHaveAttribute(
        "href",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
      );
    });

    it("does not show YouTube badge when preview_url is present", () => {
      const previewTrack = {
        ...MOCK_TRACK,
        preview_url: "https://cdn.example.com/preview.mp3",
        youtube_id: "dQw4w9WgXcQ",
      };
      render(
        <TrackScrollCard track={previewTrack} isActive={false} data-index={0} />
      );
      expect(screen.queryByText(/watch on youtube/i)).not.toBeInTheDocument();
    });
  });

  describe("active state", () => {
    it("applies active CSS class when isActive is true", () => {
      const { container } = render(
        <TrackScrollCard track={MOCK_TRACK} isActive={true} data-index={0} />
      );
      expect(container.firstChild.className).toContain("scroll-card--active");
    });

    it("does not apply active class when isActive is false", () => {
      const { container } = render(
        <TrackScrollCard track={MOCK_TRACK} isActive={false} data-index={0} />
      );
      expect(container.firstChild.className).not.toContain("scroll-card--active");
    });
  });
});
