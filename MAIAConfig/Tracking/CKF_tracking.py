import os

from GaudiKernel.Constants import INFO, WARNING, DEBUG
from Configurables import CKFTrackingAlg, ACTSDuplicateRemoval, FilterTracksAlg, TrackTruthAlg, RefitFinal
from Common.muc_mt import get_mt_args

def CKFTracker_cfg(args):
    """
    Create a new CKFTrackingAlg instance for CKF tracking.
    """
    # Time-aware (4D) seeding cuts, controlled via environment variables so the
    # CPU-impact scan can vary them without editing the config. A value of -1
    # disables the cut (3D seeding), matching the upstream default behaviour.
    seedDeltaTMax = float(os.environ.get("SEED_DELTATMAX", "-1"))
    # 4D CKF: include the hit time as a 3rd measurement dimension (eBoundTime) in
    # the Kalman filter/smoother. Off by default; enable with USE_HITTIME_CKF=1.
    # HITTIME_RESOLUTION (ns) sets the per-hit time measurement uncertainty.
    useHitTimeInCKF = os.environ.get("USE_HITTIME_CKF", "0").lower() not in ("0", "false", "no", "")
    hitTimeResolution = float(os.environ.get("HITTIME_RESOLUTION", "0.10"))
    useBranchStopper = os.environ.get("USE_BRANCHSTOPPER", "1").lower() not in ("0", "false", "no", "")
    chi2CutOff = float(os.environ.get("CKF_CHI2", "12"))
    chi2CutOffOutlier = float(os.environ.get("CKF_CHI2_OUTLIER", "25"))
    return CKFTrackingAlg(
        "Reconstructor",
        RunCKF = True,
        CKF_Chi2CutOff = chi2CutOff,
        # Hits with chi2CutOff <= local chi2 < chi2CutOffOutlier are kept as outliers; above -> hole.
        CKF_Chi2CutOffOutlier = chi2CutOffOutlier,
        # CKF branch stopper: terminate fake branches early instead of extending
        # them through the whole detector.
        UseBranchStopper = useBranchStopper,
        BranchStopper_MaxHoles = 2,              # aligned with downstream FilterTracksAlg
        BranchStopper_MaxOutliers = 3,
        BranchStopper_MinMeasurements = 8,       # aligned with downstream (>=8 hits)
        BranchStopper_PtMin = 0.5,              # GeV; drop branches falling below
        BranchStopper_PtMinMeasurements = 4,
        SeedFinding_RMax = 150,
        SeedFinding_MinPt = 500,
        SeedFinding_ImpactMax = 3,
        CKF_NumMeasurementsCutOff = 1,
        SeedFinding_SigmaScattering = 50,
        SeedFinding_CollisionRegion = 6,
        SeedFinding_RadLengthPerSeed = 0.1,
        SeedFinding_DeltaTMax = seedDeltaTMax,
        UseHitTimeInCKF = useHitTimeInCKF,
        HitTimeResolution = hitTimeResolution,
        SeedingSensorsCellIDs = ["system:1", "system:2,layer:1|2|3"],
        OutputTrackCollection = "AllTracks",
        OutputSeedCollection = "SeedTracks",
        InputTrackerHitCollection = "MergedTrackerHits",
        InputTrackerHitRelationCollection = "MergedTrackerHitsRelations",
        NumThreads = get_mt_args().numThreads,
        OutputLevel = INFO,
    )

def deduper_cfg():
    """
    Create a new ACTSDuplicateRemoval instance for removing duplicate tracks.
    """
    return ACTSDuplicateRemoval(
        "Deduper",
        InputTrackCollectionName = ["AllTracks"],
        OutputTrackCollectionName = ["DedupedTracks"],
        OutputLevel = INFO
    )


def track_filter_cfg():
    """
    Create a new FilterTracksAlg instance for filtering tracks.
    """
    # Max holes on a filtered track; <0 disables the cut. Env-controlled so the
    # scan can turn it off for the nominal (no-outlier-cut) configuration.
    filterMaxHoles = int(os.environ.get("FILTER_MAXHOLES", "2"))
    return FilterTracksAlg(
        "Filterer",
        InputTrackCollectionName = ["DedupedTracks"],
        MinPt = "0.5",
        MaxD0 = 10,
        MaxZ0 = 10,
        NHitsInner = "0",
        NHitsOuter = "0",
        NHitsTotal = "7",
        NHitsVertex = "0",
        MaxHoles = filterMaxHoles,
        OutputTrackCollectionName = ["SiTracks"],
        OutputLevel = INFO
    )

def track_truth_cfg(args):
    """
    Create a new TrackTruth instance for track truth matching.
    """
    return TrackTruthAlg(
        "TruthMatcher",
        NumThreads = get_mt_args().numThreads,
        InputTrackCollectionName = ["SiTracks"],
        InputTrackerHit2SimTrackerHitRelationName = ["MergedTrackerHitsRelations"],
        OutputParticle2TrackRelationName = ["SiTrackRelations"],
        OutputLevel = INFO
    )

def track_refitter_cfg():
    """
    Create a new TrackRefitter instance for refitting tracks.
    """
    return RefitFinal(
        "Refitter",
#        DoCutsOnRedChi2Nhits = True,
        EnergyLossOn = True,
        InputRelationCollectionName = ["SiTrackRelations"],
        InputTrackCollectionName = ["SiTracks"],
        Max_Chi2_Incr = 1.79769e+30,
        MinClustersOnTrackAfterFit = 3,
        MultipleScatteringOn = True,
#        NHitsCuts = ["1,2", "1", "3,4", "1", "5,6", "0"],
        OutputRelationCollectionName = ["SiTracks_Refitted_Relation"],
        OutputTrackCollectionName = ["SiTracks_Refitted"],
#        ReducedChi2Cut = 10.,
        ReferencePoint = -1,
        SmoothOn = False,
        extrapolateForward = True,
        OutputLevel = INFO
    )
