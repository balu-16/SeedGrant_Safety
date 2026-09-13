import { useRef, useState } from "react";
import {
  ScrollView,
  View,
  useWindowDimensions,
  NativeScrollEvent,
  NativeSyntheticEvent,
  Pressable,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { router } from "expo-router";
import {
  Brand,
  Button,
  Hero,
  LinkText,
  Txt,
  Waves,
  s,
} from "../../components/ui";
import { useApp } from "../../store/AppStore";
import { C } from "../../constants/theme";
const slides = [
  {
    title: "Stay safe wherever you go",
    subtitle: "Real-time location. Greater peace of mind.",
  },
  {
    title: "Share your live location instantly",
    subtitle: "Your trusted guardians stay updated in real time.",
  },
  {
    title: "Get help in seconds when it matters",
    subtitle: "Tap SOS to instantly alert your guardians.",
  },
];
export default function OnboardingScreen() {
  const { width, height } = useWindowDimensions();
  const pageWidth = Math.min(width, 600);
  const [page, setPage] = useState(0);
  const scroll = useRef<ScrollView>(null);
  const { dispatch } = useApp();
  const complete = () => {
    dispatch({ type: "onboard" });
    router.replace("/login");
  };
  const changePage = (index: number) => {
    setPage(index);
    scroll.current?.scrollTo({ x: index * pageWidth, animated: true });
  };
  const onScroll = (e: NativeSyntheticEvent<NativeScrollEvent>) =>
    setPage(
      Math.max(
        0,
        Math.min(2, Math.round(e.nativeEvent.contentOffset.x / pageWidth)),
      ),
    );
  return (
    <SafeAreaView style={s.page}>
      <View style={{ flex: 1, width: pageWidth, alignSelf: "center" }}>
        <View style={{ paddingTop: height > 740 ? 30 : 4 }}>
          <Brand />
        </View>
        <ScrollView
          ref={scroll}
          horizontal
          pagingEnabled
          showsHorizontalScrollIndicator={false}
          onMomentumScrollEnd={onScroll}
          onScroll={onScroll}
          scrollEventThrottle={16}
          style={{ flexGrow: 0 }}
          contentOffset={{ x: 0, y: 0 }}
        >
          {slides.map((slide, i) => (
            <View key={slide.title} style={{ width: pageWidth }}>
              <Hero
                index={i}
                height={Math.min(pageWidth * 0.88, height * 0.44)}
              />
              <View
                style={{
                  paddingHorizontal: 17,
                  paddingTop: 14,
                  gap: 9,
                  alignItems: "center",
                  minHeight: 112,
                }}
              >
                <Txt
                  accessibilityRole="header"
                  style={{
                    fontSize:
                      Math.min(pageWidth / 390, 1.3) * [25, 22, 20.5][i],
                    fontWeight: "700",
                    textAlign: "center",
                    letterSpacing: -0.7,
                  }}
                >
                  {slide.title}
                </Txt>
                <Txt
                  style={{
                    color: C.muted,
                    textAlign: "center",
                    fontSize: 15,
                    lineHeight: 22,
                  }}
                >
                  {slide.subtitle}
                </Txt>
              </View>
            </View>
          ))}
        </ScrollView>
        <View style={{ flex: 1, minHeight: 25, marginTop: 2 }}>
          <Waves />
        </View>
        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
            padding: 22,
            paddingBottom: 20,
          }}
        >
          <LinkText title="Skip" onPress={complete} />
          <View
            style={{
              position: "absolute",
              left: "50%",
              marginLeft: -37.5,
              flexDirection: "row",
              gap: 0,
            }}
          >
            {slides.map((_, i) => (
              <Pressable
                key={i}
                accessibilityRole="button"
                accessibilityLabel={`Go to slide ${i + 1}`}
                accessibilityState={{ selected: page === i }}
                aria-selected={page === i}
                onPress={() => changePage(i)}
                style={{ padding: 7 }}
              >
                <View
                  style={{
                    width: 11,
                    height: 11,
                    borderRadius: 7,
                    backgroundColor: i === page ? C.blue : "#CEDCEF",
                  }}
                />
              </Pressable>
            ))}
          </View>
          <Button
            title="Next"
            icon="chevron-forward"
            onPress={() => (page === 2 ? complete() : changePage(page + 1))}
          />
        </View>
      </View>
    </SafeAreaView>
  );
}
