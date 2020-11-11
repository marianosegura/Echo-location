from math import radians, degrees
from ray import Ray
from unit_vector import UnitVector
from angle_range import AngleRange


class RayGenerator:
    """ Generator of rays. Handles methods regarding generation of rays and their energy loss by bouncing or distance traveling.

        Attributes:
                secondary_rays_number (int): Number of rays created by a sonar sound shoot or reflection.
                spotlight_rays (int): Number of companion rays generated by the creation of a ray.
                spotlight_base_energy_factor (float): Percentage of the source ray energy passed to the spotlight rays.
                spotlight_degrees_range (int): Degrees of deviation of the spotlight rays from their main ray. Resembling a spotlight shape.
                energy_loss_per_degree (float): Amount of energy lost by degree deviation from a reference angle. Used to calculate bounce and secondary ray energy.
                energy_loss_per_pixel_traveled (float): Amount of energy lost by pixel traveled. Used upon sonar hit to calculate the final energy.
    """
    secondary_rays_number = 8
    spotlight_rays = 12
    spotlight_base_energy_factor = 0.35
    spotlight_degrees_range = 30
    energy_loss_per_degree = 0.3
    energy_loss_per_pixel_traveled = 0.05


    @staticmethod
    def get_initial_sonar_rays(sonar_point, range_angle):
        """Returns the initial rays coming out of sonar.

            Args:
                sonar_point (:obj:`Point`): sonar center point.
                range_angle (:obj:`AngleRange`): sonar sight range in radians

            Returns:
                :obj:`list` of :obj:`Ray`: primary rays
        """
        rays = []
        for i in range(RayGenerator.secondary_rays_number):
            angle = range_angle.get_random_angle_in_range()
            ray = Ray(degrees(angle), UnitVector(sonar_point, angle))
            rays.append(ray)
        return rays


    @staticmethod
    def get_spotlight_rays(primary_ray):
        """Generates self.spotlight_rays spotlight rays from a primary ray.

            Args:
                primary_ray (:obj:`Ray`): ray from which the spotlight rays come out

            Returns:
                :obj:`list` of `Ray`: spotlight rays for the primary ray
        """
        min_angle = degrees(primary_ray.vector.angle) - RayGenerator.spotlight_degrees_range
        max_angle = degrees(primary_ray.vector.angle) + RayGenerator.spotlight_degrees_range

        min_angle = (360 + min_angle) if (min_angle < 0) else min_angle # adjust negative angle
        max_angle = (max_angle - 360) if (max_angle > 360) else max_angle # adjust over 360 angle

        angle_range = AngleRange(radians(min_angle), radians(max_angle))

        sonar_angle = primary_ray.angle_from_sonar
        base_energy = primary_ray.energy * RayGenerator.spotlight_base_energy_factor
        distance = primary_ray.traveled_distance
        bounces = primary_ray.bounces
        origin_point = primary_ray.vector.origin_point

        rays = []
        for i in range(RayGenerator.spotlight_rays):
            ray_angle = angle_range.get_random_angle_in_range()
            energy = RayGenerator.get_energy_with_degrees_loss(base_energy, degrees(primary_ray.vector.angle), degrees(ray_angle))
            if energy > 0:
                ray_vector = UnitVector(origin_point, ray_angle)
                ray = Ray(sonar_angle, ray_vector, energy, distance, bounces)
                rays.append(ray)
        return rays


    @staticmethod
    def get_secondary_rays(primary_ray, range_angle):
        """Generates secondary ray in a range_angle, from a primary ray

            Args:
                primary_ray (:obj:`Ray`): ray from which the secondary rays come out
                range_angle (:obj:`AngleRange`): range in radians for secondary angles

            Returns:
                :obj:`list` of `Ray`: secondary rays
        """
        sonar_from_angle = primary_ray.angle_from_sonar
        rays=[]
        for i in range(RayGenerator.secondary_rays_number):
            angle=range_angle.get_random_angle_in_range()
            point=primary_ray.vector.origin_point
            energy = RayGenerator.get_energy_with_degrees_loss(primary_ray.energy, degrees(primary_ray.vector.angle), degrees(angle))

            if energy > 0:
                ray=Ray(sonar_from_angle, UnitVector(point,angle),energy,primary_ray.traveled_distance)
                rays.append(ray)
        return rays


    @staticmethod
    def get_energy_with_degrees_loss(source_energy, source_degrees, ray_degrees):
        """Returns the energy with loss according to a source energy and angle in degrees.
           The further the ray angle is from the source, the less energy it will have.

            Args:
                source_energy (float): Energy of the source ray.
                source_degrees (float): Angle of the source ray in degrees.
                ray_degrees (float): Angle of the ray being calculated in degrees.

            Returns:
                int: Energy of the ray being calculated with loss.
        """
        degrees_difference = RayGenerator.get_degrees_difference(source_degrees, ray_degrees)
        return source_energy - degrees_difference * RayGenerator.energy_loss_per_degree


    @staticmethod
    def get_degrees_difference(angle_a, angle_b):
        """Returns the difference between two angles in degrees. If one angle is in the first quadrant
           and the other is in the fourth quadrant, the angle return is the one between within those quadrants.

            Args:
                angle_a (int): First angle in degrees.
                angle_b (int): Second angle in degrees.

            Returns:
                int: Difference between the angles.
        """
        between_first_and_fourth_quadrant = (angle_a < 90 and angle_b > 270 or angle_b < 90 and angle_a > 270)
        if between_first_and_fourth_quadrant:
            angle_a = (360 - angle_a) if (angle_a > 270) else angle_a # adjust the over 270 angle
            angle_b = (360 - angle_b) if (angle_b > 270) else angle_b
            return angle_a + angle_b
        else:
            return abs(angle_a - angle_b)


    @staticmethod
    def get_reflected_ray(source_ray, line_segment):
        """Returns ray reflected from a line segment and a source ray.

            Args:
                source_ray (:obj:`Ray`): Ray the hits the line segment.
                line_segment (:obj:`LineSegment`): Line segment being hit.

            Returns:
                int: Energy with distance traveled loss.
        """
        reflection_point = line_segment.get_intersection_point(source_ray.vector)
        reflected_vector = line_segment.get_reflected_vector(reflection_point, source_ray.vector)
        traveled_distance = source_ray.traveled_distance + reflection_point.get_distance_to(source_ray.vector.origin_point)
        bounces = source_ray.bounces + 1

        degrees_from_reflection_point_to_source_ray_origin = degrees(reflected_vector.origin_point.get_angle_to(source_ray.vector.origin_point))

        energy = line_segment.get_energy_with_absorption_loss(source_ray.energy)
        energy = RayGenerator.get_energy_with_degrees_loss(energy, degrees_from_reflection_point_to_source_ray_origin, degrees(reflected_vector.angle))

        reflected_ray = Ray(source_ray.angle_from_sonar, reflected_vector, energy, traveled_distance, bounces)
        return reflected_ray


    @staticmethod
    def get_returning_reflected_ray(reflected_ray, source_ray):
        """Returns the ray that returns in the direction of a source ray after a ray reflection.
           On each reflection this ray is always created.

            Args:
                reflected_ray (:obj:`Ray`): Ray reflected from the source ray hitting the line segment.
                source_ray (:obj:`Ray`): Ray the hits the line segment.

            Returns:
                :obj:`Ray`: Ray going from the reflection point to the source ray origin direction.
        """
        angle = (reflected_ray.vector.origin_point).get_angle_to(source_ray.vector.origin_point)
        energy = RayGenerator.get_energy_with_degrees_loss(reflected_ray.energy, degrees(angle), degrees(reflected_ray.vector.angle))
        vector = UnitVector(reflected_ray.vector.origin_point, angle)
        returning_ray = Ray(source_ray.angle_from_sonar, vector, energy, reflected_ray.traveled_distance, reflected_ray.bounces)
        return returning_ray


    @staticmethod
    def get_energy_with_distance_loss(source_energy, traveled_distance):
        """Returns the energy with loss according to the distance traveled by a ray.
           The larger the distance, the smaller the energy.

            Args:
                source_energy (float): Energy of the source ray.
                traveled_distance (float): Distance traveled by the source ray.

            Returns:
                int: Energy with distance traveled loss.
        """
        return source_energy - traveled_distance * RayGenerator.energy_loss_per_pixel_traveled
